'use client'

import React, { useState } from 'react'
import { useUSBSerial, SerialPort } from '@/app/lib/usb_serial_service'

interface USBConnectionPanelProps {
  onConnect?: (port: string) => void
  onDisconnect?: () => void
  connectedPort?: string | null
}

export default function USBConnectionPanel({
  onConnect,
  onDisconnect,
  connectedPort: externalConnectedPort,
}: USBConnectionPanelProps) {
  const {
    ports,
    connectedPort,
    loading,
    error,
    refreshPorts,
    connectToPort,
    disconnectFromPort,
    autoDetectDrone,
  } = useUSBSerial()

  const [selectedPort, setSelectedPort] = useState<string>('')
  const [baudrate, setBaudrate] = useState<number>(57600)
  const [showPanel, setShowPanel] = useState(false)

  const activeConnectedPort = externalConnectedPort || connectedPort

  const handleAutoDetect = async () => {
    const result = await autoDetectDrone()
    if (result?.detected && result.port) {
      setSelectedPort(result.port)
    }
  }

  const handleConnect = async () => {
    if (!selectedPort) return
    
    const success = await connectToPort(selectedPort, baudrate)
    if (success && onConnect) {
      onConnect(selectedPort)
    }
  }

  const handleDisconnect = async () => {
    if (!activeConnectedPort) return
    
    const success = await disconnectFromPort(activeConnectedPort)
    if (success && onDisconnect) {
      onDisconnect()
    }
  }

  if (!showPanel) {
    return (
      <button
        onClick={() => setShowPanel(true)}
        className="fixed bottom-4 left-4 z-50 px-4 py-2 bg-blue-600 text-white rounded-lg shadow-lg hover:bg-blue-700 transition-all"
      >
        {activeConnectedPort ? '🔌 USB已连接' : '🔌 连接USB'}
      </button>
    )
  }

  return (
    <div className="fixed bottom-4 left-4 z-50 bg-white rounded-xl shadow-2xl p-6 w-80 border border-gray-200">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          📡 USB串口连接
        </h3>
        <button
          onClick={() => setShowPanel(false)}
          className="text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
          {error}
        </div>
      )}

      {activeConnectedPort ? (
        <div className="space-y-4">
          <div className="flex items-center gap-2 p-3 bg-green-50 border border-green-200 rounded-lg">
            <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
            <span className="text-green-700 font-medium">
              已连接: {activeConnectedPort}
            </span>
          </div>
          
          <button
            onClick={handleDisconnect}
            disabled={loading}
            className="w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-all"
          >
            {loading ? '断开中...' : '断开连接'}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              自动检测无人机
            </label>
            <button
              onClick={handleAutoDetect}
              disabled={loading}
              className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-all"
            >
              {loading ? '检测中...' : '🔍 自动检测'}
            </button>
          </div>

          <div className="h-px bg-gray-200"></div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              串口列表
              <button
                onClick={refreshPorts}
                className="ml-2 text-blue-600 hover:text-blue-800"
              >
                ↻
              </button>
            </label>
            <select
              value={selectedPort}
              onChange={(e) => setSelectedPort(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">选择串口...</option>
              {ports.map((port) => (
                <option key={port.device} value={port.device}>
                  {port.device} - {port.description}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              波特率
            </label>
            <select
              value={baudrate}
              onChange={(e) => setBaudrate(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value={9600}>9600</option>
              <option value={57600}>57600 (推荐)</option>
              <option value={115200}>115200</option>
            </select>
          </div>

          <button
            onClick={handleConnect}
            disabled={!selectedPort || loading}
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {loading ? '连接中...' : '🔌 连接'}
          </button>
        </div>
      )}

      {ports.length === 0 && !activeConnectedPort && (
        <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-700 text-sm">
          💡 提示: 请先将无人机通过USB连接到电脑
        </div>
      )}
    </div>
  )
}
