'use client'

import { useState, useEffect, useCallback } from 'react'

const API_BASE = 'http://localhost:8000'

export interface SerialPort {
  device: string
  description: string
  hardware_id: string
  vendor_id?: number
  product_id?: number
}

export interface ConnectionStatus {
  port: string
  baudrate: number
  connected: boolean
  last_activity?: string
}

export interface AutoDetectResult {
  success: boolean
  detected: boolean
  port?: string
  description?: string
  suggested_baudrates?: number[]
  ports?: string[]
  message?: string
}

export class USBSerialService {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE) {
    this.baseUrl = baseUrl
  }

  async listPorts(): Promise<SerialPort[]> {
    const response = await fetch(`${this.baseUrl}/api/usb/ports`)
    if (!response.ok) {
      throw new Error('Failed to list ports')
    }
    return response.json()
  }

  async connect(port: string, baudrate: number = 57600): Promise<{
    success: boolean
    message: string
    port: string
    baudrate: number
  }> {
    const response = await fetch(`${this.baseUrl}/api/usb/connect`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ port, baudrate }),
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to connect')
    }
    return response.json()
  }

  async disconnect(port: string): Promise<{
    success: boolean
    message: string
  }> {
    const response = await fetch(`${this.baseUrl}/api/usb/disconnect?port=${encodeURIComponent(port)}`, {
      method: 'POST',
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to disconnect')
    }
    return response.json()
  }

  async getStatus(port: string): Promise<ConnectionStatus> {
    const response = await fetch(`${this.baseUrl}/api/usb/status/${encodeURIComponent(port)}`)
    if (!response.ok) {
      throw new Error('Failed to get status')
    }
    return response.json()
  }

  async getAllConnections(): Promise<{
    connections: ConnectionStatus[]
    count: number
  }> {
    const response = await fetch(`${this.baseUrl}/api/usb/connections`)
    if (!response.ok) {
      throw new Error('Failed to get connections')
    }
    return response.json()
  }

  async sendData(port: string, data: string | object): Promise<{
    success: boolean
    message: string
  }> {
    const payload: any = { port }
    
    if (typeof data === 'object') {
      payload.json_data = data
    } else {
      payload.data = data
    }

    const response = await fetch(`${this.baseUrl}/api/usb/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to send data')
    }
    return response.json()
  }

  async receiveData(port: string, timeout: number = 1.0): Promise<{
    success: boolean
    data?: string
    raw?: string
    message?: string
  }> {
    const response = await fetch(
      `${this.baseUrl}/api/usb/receive/${encodeURIComponent(port)}?timeout=${timeout}`
    )
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to receive data')
    }
    return response.json()
  }

  async autoDetect(): Promise<AutoDetectResult> {
    const response = await fetch(`${this.baseUrl}/api/usb/auto-detect`, {
      method: 'POST',
    })
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to auto-detect')
    }
    return response.json()
  }
}

export const usbSerialService = new USBSerialService()

export function useUSBSerial() {
  const [ports, setPorts] = useState<SerialPort[]>([])
  const [connectedPort, setConnectedPort] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refreshPorts = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const portList = await usbSerialService.listPorts()
      setPorts(portList)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to list ports')
    } finally {
      setLoading(false)
    }
  }, [])

  const connectToPort = useCallback(async (port: string, baudrate: number = 57600) => {
    setLoading(true)
    setError(null)
    try {
      await usbSerialService.connect(port, baudrate)
      setConnectedPort(port)
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to connect')
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  const disconnectFromPort = useCallback(async (port: string) => {
    setLoading(true)
    setError(null)
    try {
      await usbSerialService.disconnect(port)
      if (connectedPort === port) {
        setConnectedPort(null)
      }
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disconnect')
      return false
    } finally {
      setLoading(false)
    }
  }, [connectedPort])

  const autoDetectDrone = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await usbSerialService.autoDetect()
      return result
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to auto-detect')
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshPorts()
    
    const interval = setInterval(refreshPorts, 5000)
    return () => clearInterval(interval)
  }, [refreshPorts])

  return {
    ports,
    connectedPort,
    loading,
    error,
    refreshPorts,
    connectToPort,
    disconnectFromPort,
    autoDetectDrone,
    usbSerialService,
  }
}
