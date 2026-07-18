import { IconText, IconChart, IconLayers } from './icons'

const TABS = [
  { id: 'input', label: 'Input', icon: IconText },
  { id: 'chart', label: 'Chart', icon: IconChart },
  { id: 'insights', label: 'Insights', icon: IconLayers },
]

function MobileTabBar({ activeTab, onTabChange, textsCount, clustersCount, selectedPoint, selectedCluster }) {
  const indicators = {
    input: textsCount > 0 ? textsCount : null,
    chart: clustersCount > 0 ? clustersCount : null,
    insights: selectedPoint || selectedCluster ? '•' : null,
  }

  return (
    <nav
      role="tablist"
      aria-label="Sections"
      className="md:hidden fixed bottom-0 inset-x-0 z-30 bg-white border-t border-gray-200 pb-safe-bottom shadow-[0_-2px_10px_rgba(0,0,0,0.04)]"
    >
      <div className="flex items-stretch">
        {TABS.map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          const indicator = indicators[tab.id]
          return (
            <button
              key={tab.id}
              role="tab"
              aria-selected={isActive}
              aria-controls={`panel-${tab.id}`}
              onClick={() => onTabChange(tab.id)}
              className={`tab-item touch-target ${isActive ? 'tab-item-active' : ''}`}
            >
              <div className="relative">
                <Icon className="w-5 h-5" />
                {indicator && (
                  <span
                    className={`absolute -top-1 -right-2 min-w-[16px] h-4 px-1 text-[10px] font-semibold rounded-full flex items-center justify-center ${
                      isActive
                        ? 'bg-primary-600 text-white'
                        : 'bg-gray-200 text-gray-600'
                    }`}
                  >
                    {indicator}
                  </span>
                )}
              </div>
              <span>{tab.label}</span>
            </button>
          )
        })}
      </div>
    </nav>
  )
}

export default MobileTabBar