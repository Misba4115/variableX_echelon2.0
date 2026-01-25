'use client'

import { useEffect, useState } from 'react'
import { getCurrentPrice, getPriceHistory, getPredictions } from '../lib/supabase'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'

export default function Dashboard() {
  // State management
  const [currentPrice, setCurrentPrice] = useState<any>(null)
  const [priceHistory, setPriceHistory] = useState<any[]>([])
  const [predictions, setPredictions] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [currency, setCurrency] = useState<'USD' | 'INR'>('USD')

  // Currency conversion rate (you can fetch this from an API later)
  const conversionRate = 83.5 // 1 USD = 83.5 INR (approximate)

  // Convert price based on selected currency
  const convertPrice = (priceInUSD: number) => {
    return currency === 'USD' ? priceInUSD : priceInUSD * conversionRate
  }

  const getCurrencySymbol = () => currency === 'USD' ? '$' : '₹'

  // Fetch data on component mount
  useEffect(() => {
    fetchData()
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  async function fetchData() {
    try {
      const [price, history, preds] = await Promise.all([
        getCurrentPrice(),
        getPriceHistory(30),
        getPredictions(10)
      ])

      setCurrentPrice(price)
      setPriceHistory(history)
      setPredictions(preds)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching data:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-slate-700 text-xl font-semibold mb-2">Loading Dashboard</div>
          <div className="text-slate-400 text-sm">Fetching market data...</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-slate-50 p-4">

      {/* Premium Header with Glass Effect */}
      <div className="max-w-7xl mx-auto mb-4">
        <div className="flex items-center justify-between bg-white/80 backdrop-blur-sm rounded-xl p-4 shadow-lg border border-slate-200/50">
          <div>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-md">
                <span className="text-white text-xl">🥈</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">Argentum Insights</h1>
                <p className="text-xs text-slate-500 flex items-center gap-1.5 mt-0.5">
                  <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse"></span>
                  Live Data
                </p>
              </div>
            </div>
          </div>

          {/* Premium Currency Toggle */}
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-500 font-medium">Currency:</span>
            <div className="flex items-center gap-1 bg-slate-100 rounded-lg p-1">
              <button
                onClick={() => setCurrency('USD')}
                className={`px-4 py-1.5 rounded-md text-sm font-semibold transition-all duration-200 ${currency === 'USD'
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
              >
                USD
              </button>
              <button
                onClick={() => setCurrency('INR')}
                className={`px-4 py-1.5 rounded-md text-sm font-semibold transition-all duration-200 ${currency === 'INR'
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
              >
                INR
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto space-y-4">

        {/* Main Content: Chart on Left, KPIs on Right */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

          {/* Price Chart - Premium Design */}
          <div className="lg:col-span-2 bg-white/80 backdrop-blur-sm border border-slate-200/50 rounded-xl p-4 shadow-lg">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h2 className="text-sm font-bold text-slate-900">Price Performance</h2>
                <p className="text-xs text-slate-500">Last 30 days</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-slate-500 bg-slate-100 px-2.5 py-1 rounded-md">Spot</span>
              </div>
            </div>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={priceHistory}>
                  <defs>
                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" strokeWidth={0.5} vertical={false} />
                  <XAxis
                    dataKey="timestamp"
                    stroke="#94a3b8"
                    tick={{ fill: '#64748b', fontSize: 10 }}
                    tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    axisLine={false}
                  />
                  <YAxis
                    stroke="#94a3b8"
                    tick={{ fill: '#64748b', fontSize: 10 }}
                    domain={['dataMin - 1', 'dataMax + 1']}
                    width={45}
                    axisLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: 'rgba(255, 255, 255, 0.95)',
                      border: '1px solid #cbd5e1',
                      borderRadius: '8px',
                      fontSize: '11px',
                      padding: '8px',
                      backdropFilter: 'blur(8px)'
                    }}
                    labelStyle={{ color: '#334155', fontWeight: 600, marginBottom: '4px' }}
                    itemStyle={{ color: '#3b82f6' }}
                  />
                  <Area
                    type="monotone"
                    dataKey="price"
                    stroke="#3b82f6"
                    strokeWidth={2.5}
                    fill="url(#colorPrice)"
                    dot={false}
                    activeDot={{ r: 5, fill: '#3b82f6', stroke: '#fff', strokeWidth: 2 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* KPI Cards - Premium Design */}
          <div className="space-y-3">

            {/* Current Price */}
            <div className="group bg-gradient-to-br from-blue-50 via-blue-50 to-indigo-100 border border-blue-200 rounded-xl p-4 shadow-lg hover:shadow-xl transition-all duration-300">
              <div className="flex items-center justify-between mb-1">
                <span className="text-blue-700 text-xs font-bold tracking-wide">CURRENT PRICE</span>
                <div className="w-8 h-8 bg-blue-500/10 rounded-lg flex items-center justify-center">
                  <span className="text-blue-600 text-sm">💰</span>
                </div>
              </div>
              <div className="text-3xl font-bold text-blue-900 tracking-tight">
                {getCurrencySymbol()}{convertPrice(currentPrice?.price || 0).toFixed(2)}
              </div>
              <div className="text-xs text-blue-600 mt-1 font-medium">Per troy ounce</div>
            </div>

            {/* 24h High */}
            <div className="group bg-gradient-to-br from-violet-50 via-violet-50 to-purple-100 border border-violet-200 rounded-xl p-4 shadow-lg hover:shadow-xl transition-all duration-300">
              <div className="flex items-center justify-between mb-1">
                <span className="text-violet-700 text-xs font-bold tracking-wide">24H HIGH</span>
                <div className="w-8 h-8 bg-violet-500/10 rounded-lg flex items-center justify-center">
                  <span className="text-violet-600 text-sm">📈</span>
                </div>
              </div>
              <div className="text-3xl font-bold text-violet-900 tracking-tight">
                {getCurrencySymbol()}{convertPrice(currentPrice?.high_24h || 0).toFixed(2)}
              </div>
              <div className="text-xs text-violet-600 mt-1 font-medium">Peak value</div>
            </div>

            {/* 24h Low */}
            <div className="group bg-gradient-to-br from-orange-50 via-orange-50 to-amber-100 border border-orange-200 rounded-xl p-4 shadow-lg hover:shadow-xl transition-all duration-300">
              <div className="flex items-center justify-between mb-1">
                <span className="text-orange-700 text-xs font-bold tracking-wide">24H LOW</span>
                <div className="w-8 h-8 bg-orange-500/10 rounded-lg flex items-center justify-center">
                  <span className="text-orange-600 text-sm">📉</span>
                </div>
              </div>
              <div className="text-3xl font-bold text-orange-900 tracking-tight">
                {getCurrencySymbol()}{convertPrice(currentPrice?.low_24h || 0).toFixed(2)}
              </div>
              <div className="text-xs text-orange-600 mt-1 font-medium">Lowest value</div>
            </div>

            {/* Price Change */}
            <div className={`group border rounded-xl p-4 shadow-lg hover:shadow-xl transition-all duration-300 ${(currentPrice?.price_change_percent || 0) >= 0
              ? 'bg-gradient-to-br from-cyan-50 via-cyan-50 to-teal-100 border-cyan-200'
              : 'bg-gradient-to-br from-rose-50 via-rose-50 to-red-100 border-rose-200'
              }`}>
              <div className="flex items-center justify-between mb-1">
                <span className={`text-xs font-bold tracking-wide ${(currentPrice?.price_change_percent || 0) >= 0 ? 'text-cyan-700' : 'text-rose-700'
                  }`}>
                  24H CHANGE
                </span>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${(currentPrice?.price_change_percent || 0) >= 0 ? 'bg-cyan-500/10' : 'bg-rose-500/10'
                  }`}>
                  <span className={`text-sm ${(currentPrice?.price_change_percent || 0) >= 0 ? 'text-cyan-600' : 'text-rose-600'
                    }`}>
                    {(currentPrice?.price_change_percent || 0) >= 0 ? '↗' : '↘'}
                  </span>
                </div>
              </div>
              <div className={`text-3xl font-bold tracking-tight ${(currentPrice?.price_change_percent || 0) >= 0 ? 'text-cyan-900' : 'text-rose-900'
                }`}>
                {(currentPrice?.price_change_percent || 0) >= 0 ? '+' : ''}
                {currentPrice?.price_change_percent?.toFixed(2) || '0.00'}%
              </div>
              <div className={`text-xs mt-1 font-medium ${(currentPrice?.price_change_percent || 0) >= 0 ? 'text-cyan-600' : 'text-rose-600'
                }`}>
                {(currentPrice?.price_change_percent || 0) >= 0 ? 'Upward trend' : 'Downward trend'}
              </div>
            </div>

          </div>
        </div>

        {/*  Predictions Panel - Premium */}
        <div className="bg-white/80 backdrop-blur-sm border border-slate-200/50 rounded-xl p-4 shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center shadow-sm">
                <span className="text-white text-sm">🤖</span>
              </div>
              <div>
                <h2 className="text-sm font-bold text-slate-900">AI Market Predictions</h2>
                <p className="text-xs text-slate-500">Machine learning analysis</p>
              </div>
            </div>
            <span className="text-xs font-medium text-slate-500 bg-slate-100 px-3 py-1.5 rounded-lg">Latest</span>
          </div>

          {predictions.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-slate-400 text-sm">No predictions available yet</div>
              <div className="text-slate-500 text-xs mt-1">Waiting for AI analysis...</div>
            </div>
          ) : (
            <div className="space-y-3">
              {predictions.map((pred) => {
                // Extract direction from prediction_value
                const direction = pred.prediction_value?.direction?.toUpperCase() || 'NEUTRAL'
                const isBullish = direction === 'BULLISH'
                const isBearish = direction === 'BEARISH'
                const directionColor = isBullish ? 'text-blue-700' : isBearish ? 'text-rose-700' : 'text-amber-700'
                const directionBg = isBullish ? 'bg-blue-50 border-blue-300' : isBearish ? 'bg-rose-50 border-rose-300' : 'bg-amber-50 border-amber-300'

                // Extract reasoning - works with any structure
                const reasoning = pred.raw_response?.reasoning || pred.reasoning_chain || 'No reasoning provided'

                return (
                  <div key={pred.id} className="bg-slate-50/50 rounded-xl p-3 border border-slate-200 hover:border-slate-300 transition-all">

                    {/* Header Row */}
                    <div className="flex items-center justify-between mb-3">
                      <div className={`px-3 py-1.5 rounded-lg border-2 font-bold text-sm ${directionBg} ${directionColor} shadow-sm`}>
                        {direction}
                      </div>

                      <div className="flex items-center gap-2">
                        <span className="text-slate-500 text-xs font-medium">Confidence</span>
                        <div className="bg-blue-100 px-2.5 py-1 rounded-lg">
                          <span className="text-lg font-bold text-blue-700">
                            {(pred.confidence_score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Analysis */}
                    <div className="mb-2">
                      <div className="text-xs font-semibold text-slate-600 mb-1.5">Analysis Summary</div>
                      <div className="bg-white rounded-lg p-3 border border-slate-200">
                        <p className="text-slate-700 text-xs leading-relaxed">
                          {reasoning}
                        </p>
                      </div>
                    </div>

                    {/* Technical Details */}
                    {pred.prediction_value && Object.keys(pred.prediction_value).length > 1 && (
                      <details className="cursor-pointer">
                        <summary className="text-xs text-slate-500 hover:text-slate-700 font-medium">
                          View technical details →
                        </summary>
                        <div className="bg-white rounded-lg p-3 mt-2 border border-slate-200">
                          <pre className="text-xs text-slate-600 overflow-x-auto whitespace-pre-wrap font-mono">
                            {JSON.stringify(pred.prediction_value, null, 2)}
                          </pre>
                        </div>
                      </details>
                    )}

                    {/* Timestamp */}
                    <div className="text-xs text-slate-400 mt-2 flex items-center gap-1">
                      <span>🕒</span>
                      {new Date(pred.created_at).toLocaleString()}
                    </div>

                  </div>
                )
              })}
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
