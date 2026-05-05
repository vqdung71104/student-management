import React from 'react'
import { useStudentLanguage } from './useStudentLanguage'

const UserGuidePage: React.FC = () => {
  const { t } = useStudentLanguage()
  const guide = t.pages.userGuide

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-md">
        <div className="bg-blue-600 text-white p-6 rounded-t-lg">
          <h1 className="text-2xl font-bold">{guide.title}</h1>
          <p className="mt-2 text-sm text-blue-50">{guide.subtitle}</p>
        </div>

        <div className="p-6 space-y-8 text-gray-700">
          <section>
            <h2 className="text-xl font-semibold text-blue-600 mb-3">{guide.sectionOverview}</h2>
            <p>{guide.overviewText}</p>
            <div className="mt-4 bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
              <p className="font-medium text-yellow-900">{guide.noteTitle}</p>
              <ul className="list-disc pl-5 mt-2 space-y-1 text-yellow-900">
                {guide.notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-blue-600 mb-3">{guide.sectionQuickFlow}</h2>
            <ol className="list-decimal pl-5 space-y-2">
              {guide.quickFlowSteps.map((step) => {
                if (typeof step === 'string') {
                  return <li key={step}>{step}</li>
                }

                const key = step.text
                if (!step.strong || step.strong.length === 0) {
                  return <li key={key}>{step.text}</li>
                }

                let remaining = step.text
                const parts: Array<{ text: string; strong: boolean }> = []
                for (const strongText of step.strong) {
                  const index = remaining.indexOf(strongText)
                  if (index === -1) {
                    continue
                  }
                  const before = remaining.slice(0, index)
                  if (before) {
                    parts.push({ text: before, strong: false })
                  }
                  parts.push({ text: strongText, strong: true })
                  remaining = remaining.slice(index + strongText.length)
                }
                if (remaining) {
                  parts.push({ text: remaining, strong: false })
                }

                return (
                  <li key={key}>
                    {parts.map((part, index) =>
                      part.strong ? <strong key={index}>{part.text}</strong> : <span key={index}>{part.text}</span>
                    )}
                  </li>
                )
              })}
            </ol>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-blue-600 mb-3">{guide.sectionStudy}</h2>
            <div className="space-y-4">
              {guide.studyBlocks.map((block) => (
                <div key={block.title}>
                  <h3 className="font-semibold text-gray-900">{block.title}</h3>
                  <p>{block.body}</p>
                </div>
              ))}
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-blue-600 mb-3">{guide.sectionPlanner}</h2>
            <div className="space-y-4">
              {guide.plannerBlocks.map((block) => (
                <div key={block.title}>
                  <h3 className="font-semibold text-gray-900">{block.title}</h3>
                  <p>{block.body}</p>
                  {block.bullets && block.bullets.length > 0 && (
                    <ul className="list-disc pl-5 mt-2 space-y-1">
                      {block.bullets.map((bullet) => (
                        <li key={bullet}>{bullet}</li>
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-blue-600 mb-3">{guide.sectionChatbot}</h2>
            <p>{guide.chatbotText}</p>
            <div className="mt-3 bg-gray-50 border border-gray-200 p-4 rounded">
              {guide.chatbotNote}
            </div>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-blue-600 mb-3">{guide.sectionSupport}</h2>
            <ul className="list-disc pl-5 space-y-1">
              {guide.supportBullets.map((item) => (
                <li key={item.title}>
                  <strong>{item.title}</strong>: {item.body}
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </div>
  )
}

export default UserGuidePage
