import { useMemo, useState } from 'react'
import { marked } from 'marked'
import { Link2, ExternalLink } from 'lucide-react'

marked.setOptions({ breaks: true, gfm: true })

interface CitedMarkdownRendererProps {
  content: string
  urlMap?: Record<string, string>
  accentColor?: string
  className?: string
}

/**
 * Pre-process markdown: replace [N] citation markers with inline HTML anchor badges.
 */
function substituteCitations(
  content: string,
  urlMap: Record<string, string>,
  accentColor: string
): string {
  if (!urlMap || Object.keys(urlMap).length === 0) return content

  return content.replace(/\[(\d+(?:,\s*\d+)*)\](?!\()/g, (_match, inner) => {
    const nums = inner.split(/[,\s]+/).filter(Boolean)
    return nums
      .map((num: string) => {
        const n = num.trim()
        const url = urlMap[n]
        if (url && url.startsWith('http')) {
          return (
            `<a href="${url}" target="_blank" rel="noopener noreferrer" ` +
            `class="citation-badge" ` +
            `style="display:inline-flex;align-items:center;justify-content:center;` +
            `min-width:20px;height:20px;border-radius:50%;` +
            `background:${accentColor};color:#fff;font-size:10px;font-weight:900;` +
            `text-decoration:none;vertical-align:super;margin:0 2px;line-height:1;` +
            `cursor:pointer;box-shadow:0 2px 6px ${accentColor}40;` +
            `padding:0 4px;transition:all 0.2s cubic-bezier(0.34,1.56,0.64,1);` +
            `border:2px solid ${accentColor}60;" ` +
            `onmouseover="this.style.transform='scale(1.3)';this.style.boxShadow='0 4px 12px ${accentColor}60';this.style.background='${accentColor}dd'" ` +
            `onmouseout="this.style.transform='scale(1)';this.style.boxShadow='0 2px 6px ${accentColor}40';this.style.background='${accentColor}'" ` +
            `title="Source [${n}]: ${url}">[${n}]</a>`
          )
        } else {
          return (
            `<sup style="display:inline-flex;align-items:center;justify-content:center;` +
            `min-width:18px;height:18px;border-radius:50%;background:#e5e7eb;` +
            `color:#4b5563;font-size:9px;font-weight:700;vertical-align:super;` +
            `margin:0 1px;padding:0 3px;border:1px solid #d1d5db;">[${n}]</sup>`
          )
        }
      })
      .join('')
  })
}

/**
 * Enhance blockquotes as styled callout/insight boxes
 */
function enhanceBlockquotes(html: string, accentColor: string): string {
  return html.replace(
    /<blockquote>([\s\S]*?)<\/blockquote>/g,
    (_match, content) => {
      return (
        `<div class="insight-callout" style="` +
        `background:linear-gradient(135deg, ${accentColor}08 0%, ${accentColor}03 100%);` +
        `border-left:4px solid ${accentColor};` +
        `border-radius:0 12px 12px 0;` +
        `padding:16px 20px;` +
        `margin:16px 0;` +
        `box-shadow:0 2px 8px ${accentColor}10;">` +
        `<div style="display:flex;align-items:flex-start;gap:10px;">` +
        `<span style="font-size:18px;line-height:1;">💡</span>` +
        `<div style="flex:1;min-width:0;">${content}</div>` +
        `</div></div>`
      )
    }
  )
}

/**
 * Enhance bold text with accent color highlights
 */
function enhanceBoldText(html: string, accentColor: string): string {
  return html.replace(
    /<strong>([\s\S]*?)<\/strong>/g,
    (_match, content) => {
      return `<strong style="color:${accentColor};font-weight:800;">${content}</strong>`
    }
  )
}

/**
 * Enhance headings with accent underlines
 */
function enhanceHeadings(html: string, accentColor: string): string {
  return html
    .replace(
      /<h3>([\s\S]*?)<\/h3>/g,
      (_match, content) =>
        `<h3 style="border-bottom:2px solid ${accentColor}30;padding-bottom:8px;margin-top:24px;margin-bottom:12px;">${content}</h3>`
    )
    .replace(
      /<h4>([\s\S]*?)<\/h4>/g,
      (_match, content) =>
        `<h4 style="color:${accentColor};margin-top:20px;margin-bottom:8px;">${content}</h4>`
    )
}

/**
 * Enhance list items with better visual markers
 */
function enhanceLists(html: string, accentColor: string): string {
  return html
    .replace(
      /<ul>/g,
      `<ul style="list-style:none;padding-left:0;">`
    )
    .replace(
      /<li>/g,
      `<li style="position:relative;padding-left:20px;margin-bottom:8px;"><span style="position:absolute;left:0;top:2px;width:8px;height:8px;border-radius:50%;background:${accentColor}40;display:inline-block;"></span>`
    )
}

/**
 * Enhance tables: wrap in overflow container, add accent-colored header borders
 */
function enhanceTables(html: string, accentColor: string): string {
  return html
    .replace(
      /<table>/g,
      `<div style="overflow-x:auto;margin:16px 0;border-radius:12px;border:1px solid #e5e7eb;"><table style="width:100%;border-collapse:collapse;">`
    )
    .replace(
      /<\/table>/g,
      `</table></div>`
    )
    .replace(
      /<thead>/g,
      `<thead style="background:#f9fafb;">`
    )
    .replace(
      /<th>/g,
      `<th style="padding:12px 16px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;color:#6b7280;border-bottom:2px solid ${accentColor}30;">`
    )
    .replace(
      /<td>/g,
      `<td style="padding:12px 16px;border-bottom:1px solid #f3f4f6;font-size:14px;">`
    )
}

export default function CitedMarkdownRenderer({
  content,
  urlMap = {},
  accentColor = '#3b82f6',
  className = '',
}: CitedMarkdownRendererProps) {
  const [showSources, setShowSources] = useState(false)

  const html = useMemo(() => {
    try {
      // Clean up content: remove the duplicate "Sources Used" section if it exists
      // as we now have the dedicated toggle button.
      // Handles: "## Sources Used", "Sources Used:", "Sources Used" followed by numbered list
      let cleanedContent = content
        .replace(/##?\s*Sources Used[\s\S]*?(?=\n\s*(?:Confidence Score|Confidence|Output|$))/i, '')
        .replace(/\n\s*Sources Used\s*:?[\s\S]*?(?=\n\s*(?:Confidence Score|Confidence|Output|$))/i, '')

      // Also remove any trailing "References:" blocks that some agents include.
      // We keep the dedicated Show Sources toggle as the single sources UI.
      cleanedContent = cleanedContent.replace(/\n\s*References\s*:\s*\n[\s\S]*$/i, '')
      
      const withCitations = substituteCitations(cleanedContent, urlMap, accentColor)
      let parsed = marked.parse(withCitations) as string
      parsed = enhanceBlockquotes(parsed, accentColor)
      parsed = enhanceBoldText(parsed, accentColor)
      parsed = enhanceHeadings(parsed, accentColor)
      parsed = enhanceLists(parsed, accentColor)
      parsed = enhanceTables(parsed, accentColor)
      return parsed
    } catch {
      return content
    }
  }, [content, urlMap, accentColor])

  const sources = useMemo(() => {
    return Object.entries(urlMap)
      .filter(([_, url]) => url && url.startsWith('http'))
      .map(([num, url]) => ({ num, url }))
      .sort((a, b) => parseInt(a.num) - parseInt(b.num))
  }, [urlMap])

  return (
    <div className={`flex flex-col ${className}`}>
      <div
        className="prose prose-sm max-w-none prose-gray prose-table:border-collapse prose-table:w-full prose-table:text-sm prose-thead:bg-gray-50 prose-th:p-3 prose-th:text-left prose-th:text-xs prose-th:font-bold prose-th:uppercase prose-th:tracking-wider prose-th:text-gray-500 prose-th:border-b prose-th:border-gray-200 prose-td:p-3 prose-td:border-b prose-td:border-gray-100 prose-tr:hover:prose-td:bg-gray-50/50"
        dangerouslySetInnerHTML={{ __html: html }}
      />

      {sources.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-100">
          <button
            onClick={() => setShowSources(!showSources)}
            className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider transition-colors hover:opacity-80 mb-3"
            style={{ color: accentColor }}
          >
            <Link2 className="w-3.5 h-3.5" />
            {showSources ? 'Hide Sources' : `Show Sources (${sources.length})`}
          </button>

          {showSources && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 animate-in fade-in slide-in-from-top-2 duration-300">
              {sources.map((src) => (
                <a
                  key={src.num}
                  href={src.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-3 py-2 rounded-xl bg-gray-50/50 border border-gray-100 hover:border-gray-200 hover:bg-gray-100/50 transition-all group"
                >
                  <div className="flex items-center gap-1.5 shrink-0">
                    <ExternalLink className="w-3 h-3 text-gray-400 group-hover:text-blue-500" />
                    <span className="font-black text-[10px] min-w-[18px] text-center px-1 rounded-md" 
                          style={{ backgroundColor: `${accentColor}20`, color: accentColor }}>
                      [{src.num}]
                    </span>
                  </div>
                  <span className="text-[11px] text-gray-600 truncate font-medium group-hover:text-gray-900">
                    {src.url.replace(/^https?:\/\/(www\.)?/, '').split('/')[0]}
                    <span className="text-gray-400 font-normal ml-1">— {src.url.split('/').pop()?.slice(0, 30) || 'Source'}</span>
                  </span>
                </a>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

