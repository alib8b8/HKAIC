'use client'

import { useState, useRef } from 'react'
import { backupService, UserBackup } from '@/app/lib/backup-service'

interface BackupPanelProps {
  currentParams: Record<string, number>
  userEmail?: string
}

export function BackupPanel({ currentParams, userEmail }: BackupPanelProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [message, setMessage] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleExportJSON = () => {
    const backup = backupService.exportBackup(
      currentParams,
      getPresets(),
      userEmail
    )
    backupService.downloadBackup(backup)
    showMessage('JSON 备份已下载！')
  }

  const handleExportCSV = () => {
    backupService.downloadCSV(currentParams)
    showMessage('CSV 备份已下载！')
  }

  const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    try {
      const backup = await backupService.importBackup(file)
      showMessage(`成功导入备份！包含 ${backup.sessions?.length || 0} 个调参记录`)
      
      setTimeout(() => {
        window.location.reload()
      }, 1500)
    } catch (error) {
      showMessage('导入失败：' + (error as Error).message)
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleClearData = () => {
    if (confirm('确定要清除所有本地数据吗？此操作不可撤销。')) {
      backupService.clearAllData()
      showMessage('所有本地数据已清除')
      setTimeout(() => {
        window.location.reload()
      }, 1000)
    }
  }

  const getPresets = () => {
    return {
      racing: {
        'Roll P': 48,
        'Roll I': 80,
        'Roll D': 37,
        'Pitch P': 50,
        'Pitch I': 85,
        'Pitch D': 40
      },
      freestyle: {
        'Roll P': 45,
        'Roll I': 80,
        'Roll D': 35,
        'Pitch P': 47,
        'Pitch I': 85,
        'Pitch D': 38
      },
      heavy: {
        'Roll P': 42,
        'Roll I': 80,
        'Roll D': 32,
        'Pitch P': 44,
        'Pitch I': 85,
        'Pitch D': 35
      }
    }
  }

  const showMessage = (msg: string) => {
    setMessage(msg)
    setTimeout(() => setMessage(''), 3000)
  }

  const sessions = backupService.getSessions()

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 hover:opacity-90 transition shadow-lg shadow-purple-500/30 flex items-center justify-center z-40"
        title="数据备份"
      >
        <span className="text-2xl">💾</span>
      </button>
    )
  }

  return (
    <div className="fixed bottom-6 right-6 w-96 bg-gray-900 rounded-2xl border border-gray-700 shadow-2xl z-50">
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <span>💾</span>
            数据备份
          </h3>
          <button
            onClick={() => setIsOpen(false)}
            className="text-gray-400 hover:text-white transition"
          >
            ✕
          </button>
        </div>

        {message && (
          <div className="mb-4 p-3 bg-green-500/10 border border-green-500/30 rounded-xl text-green-400 text-sm">
            {message}
          </div>
        )}

        <div className="space-y-3">
          <button
            onClick={handleExportJSON}
            className="w-full py-3 rounded-xl font-medium bg-gradient-to-r from-cyan-400 to-purple-500 hover:opacity-90 transition flex items-center justify-center gap-2"
          >
            <span>📦</span>
            导出 JSON 备份
          </button>

          <button
            onClick={handleExportCSV}
            className="w-full py-3 rounded-xl font-medium bg-gray-800 hover:bg-gray-700 transition flex items-center justify-center gap-2 border border-gray-600"
          >
            <span>📊</span>
            导出 CSV 参数
          </button>

          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json"
              onChange={handleImport}
              className="hidden"
              id="backup-import"
            />
            <label
              htmlFor="backup-import"
              className="w-full py-3 rounded-xl font-medium bg-gray-800 hover:bg-gray-700 transition flex items-center justify-center gap-2 border border-gray-600 cursor-pointer"
            >
              <span>📂</span>
              导入备份文件
            </label>
          </div>

          <button
            onClick={handleClearData}
            className="w-full py-3 rounded-xl font-medium bg-red-500/10 text-red-400 hover:bg-red-500/20 transition border border-red-500/30"
          >
            <span>🗑️</span>
            清除本地数据
          </button>
        </div>

        {sessions.length > 0 && (
          <div className="mt-6 pt-6 border-t border-gray-700">
            <h4 className="text-sm font-semibold mb-3 text-gray-400">
              本地调参记录 ({sessions.length} 个)
            </h4>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {sessions.slice(-5).reverse().map((session, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-gray-800/50 rounded-xl border border-gray-700"
                >
                  <div className="text-sm font-medium">
                    {new Date(session.startTime).toLocaleString('zh-CN')}
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {session.snapshots.length} 个参数快照 • {session.conversations.length} 条对话
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="px-6 py-4 bg-gray-800/50 rounded-b-2xl border-t border-gray-700">
        <p className="text-xs text-gray-500 text-center">
          💡 备份包含您的参数配置、调参历史和对话记录
        </p>
      </div>
    </div>
  )
}
