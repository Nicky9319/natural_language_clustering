import { useEffect } from 'react'
import { IconClose } from './icons'

function BottomSheet({ open, onClose, title, children }) {
  useEffect(() => {
    if (!open) return

    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    const prevOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = prevOverflow
    }
  }, [open, onClose])

  if (!open) return null

  return (
    <div className="md:hidden fixed inset-0 z-50">
      <div
        className="bottom-sheet-backdrop"
        onClick={onClose}
        aria-hidden="true"
      />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="bottom-sheet"
      >
        <div className="bottom-sheet-handle" aria-hidden="true" />
        <div className="flex items-center justify-between px-4 pb-3 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">{title}</h2>
          <button
            type="button"
            onClick={onClose}
            className="btn-icon"
            aria-label="Close"
          >
            <IconClose className="w-5 h-5" />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-4">
          {children}
        </div>
      </div>
    </div>
  )
}

export default BottomSheet