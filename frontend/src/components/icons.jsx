// Shared icon components for consistency.
// All icons use strokeWidth=1.75 for a refined, uniform appearance.

const baseProps = {
  fill: 'none',
  stroke: 'currentColor',
  viewBox: '0 0 24 24',
  strokeLinecap: 'round',
  strokeLinejoin: 'round',
}

export function IconPlus(props) {
  return (
    <svg {...baseProps} strokeWidth={1.75} {...props}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  )
}

export function IconClose(props) {
  return (
    <svg {...baseProps} strokeWidth={1.75} {...props}>
      <path d="M6 18L18 6M6 6l12 12" />
    </svg>
  )
}

export function IconTrash(props) {
  return (
    <svg {...baseProps} strokeWidth={1.75} {...props}>
      <path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14zM10 11v6M14 11v6" />
    </svg>
  )
}

export function IconBolt(props) {
  return (
    <svg {...baseProps} strokeWidth={1.75} {...props}>
      <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
    </svg>
  )
}

export function IconChart(props) {
  return (
    <svg {...baseProps} strokeWidth={1.75} {...props}>
      <path d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
      <path d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
    </svg>
  )
}

export function IconLayers(props) {
  return (
    <svg {...baseProps} strokeWidth={1.75} {...props}>
      <path d="M12 2L2 7l10 5 10-5-10-5z" />
      <path d="M2 17l10 5 10-5M2 12l10 5 10-5" />
    </svg>
  )
}

export function IconSettings(props) {
  return (
    <svg {...baseProps} strokeWidth={1.75} {...props}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 11-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 110-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 114 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 110 4h-.09a1.65 1.65 0 00-1.51 1z" />
    </svg>
  )
}

export function IconText(props) {
  return (
    <svg {...baseProps} strokeWidth={1.75} {...props}>
      <path d="M4 6h16M4 12h16M4 18h10" />
    </svg>
  )
}

export function IconInfo(props) {
  return (
    <svg {...baseProps} strokeWidth={1.75} {...props}>
      <circle cx="12" cy="12" r="10" />
      <path d="M12 16v-4M12 8h.01" />
    </svg>
  )
}

export function IconSparkles(props) {
  return (
    <svg {...baseProps} strokeWidth={1.75} {...props}>
      <path d="M5 3v4M3 5h4M6 17v4M4 19h4M13 3l1.5 4.5L19 9l-4.5 1.5L13 15l-1.5-4.5L7 9l4.5-1.5L13 3z" />
    </svg>
  )
}

export function IconMenu(props) {
  return (
    <svg {...baseProps} strokeWidth={1.75} {...props}>
      <path d="M3 12h18M3 6h18M3 18h18" />
    </svg>
  )
}

export function IconChevronRight(props) {
  return (
    <svg {...baseProps} strokeWidth={1.75} {...props}>
      <path d="M9 18l6-6-6-6" />
    </svg>
  )
}

export function IconChevronDown(props) {
  return (
    <svg {...baseProps} strokeWidth={1.75} {...props}>
      <path d="M6 9l6 6 6-6" />
    </svg>
  )
}

export function IconCheck(props) {
  return (
    <svg {...baseProps} strokeWidth={1.75} {...props}>
      <path d="M20 6L9 17l-5-5" />
    </svg>
  )
}

export function IconAlert(props) {
  return (
    <svg {...baseProps} strokeWidth={1.75} {...props}>
      <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
      <path d="M12 9v4M12 17h.01" />
    </svg>
  )
}

export function IconSpinner(props) {
  return (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" className="opacity-25" />
      <path
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        className="opacity-75"
      />
    </svg>
  )
}

export function IconTarget(props) {
  return (
    <svg {...baseProps} strokeWidth={1.75} {...props}>
      <circle cx="12" cy="12" r="10" />
      <circle cx="12" cy="12" r="6" />
      <circle cx="12" cy="12" r="2" />
    </svg>
  )
}