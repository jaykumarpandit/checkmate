"use client"

import * as React from "react"

type RichPasteAreaProps = {
	value?: string
	placeholder?: string
	className?: string
	onChange?: (html: string) => void
}

export function RichPasteArea({ value, placeholder, className, onChange }: RichPasteAreaProps) {
	const [html, setHtml] = React.useState<string>(value ?? "")
	const ref = React.useRef<HTMLDivElement | null>(null)

	React.useEffect(() => {
		if (value !== undefined && value !== html) {
			setHtml(value)
			if (ref.current) ref.current.innerHTML = value
		}
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [value])

	const handleInput = React.useCallback(() => {
		const nextHtml = ref.current?.innerHTML ?? ""
		setHtml(nextHtml)
		onChange?.(nextHtml)
	}, [onChange])

	const handlePaste = React.useCallback((event: React.ClipboardEvent<HTMLDivElement>) => {
		// Preserve formatting by using the HTML clipboard payload
		event.preventDefault()
		const pastedHtml = event.clipboardData.getData("text/html")
		const fallbackText = event.clipboardData.getData("text/plain").replaceAll("\n", "<br>")
		const content = pastedHtml || fallbackText
		if (document) {
			const selection = window.getSelection()
			if (!selection || selection.rangeCount === 0) {
				ref.current!.insertAdjacentHTML("beforeend", content)
			} else {
				const range = selection.getRangeAt(0)
				range.deleteContents()
				const temp = document.createElement("div")
				temp.innerHTML = content
				const fragment = document.createDocumentFragment()
				while (temp.firstChild) fragment.appendChild(temp.firstChild)
				range.insertNode(fragment)
				range.collapse(false)
			}
			handleInput()
		}
	}, [handleInput])

	return (
		<div
			ref={ref}
			className={[
				"min-h-40 w-full rounded-md border border-input bg-transparent px-3 py-2 text-base shadow-xs outline-none md:text-sm",
				"focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]",
				"prose prose-sm max-w-none dark:prose-invert",
				className ?? "",
			].join(" ")}
			contentEditable
			role="textbox"
			aria-multiline
			data-slot="rich-paste-area"
			suppressContentEditableWarning
			onInput={handleInput}
			onPaste={handlePaste}
			placeholder={undefined}
			data-placeholder={placeholder}
		>
			{html ? undefined : (
				<span className="pointer-events-none select-none text-muted-foreground">{placeholder}</span>
			)}
		</div>
	)
}


