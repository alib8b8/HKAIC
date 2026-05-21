'use client';

import { useState, useRef, useEffect } from 'react';
import { useAuth } from './lib/auth-context';
import { AuthModal } from '@/components/AuthModal';
import USBConnectionPanel from '@/components/USBConnectionPanel';
import { useUSBSerial } from './lib/usb_serial_service';

interface Message {
  id: number;
  content: string;
  isUser: boolean;
  timestamp: Date;
}

interface DroneParam {
  name: string;
  value: number;
  min: number;
  max: number;
  step: number;
  unit: string;
  description: string;
}

const initialParams: DroneParam[] = [
  { name: 'Roll P', value: 45, min: 30, max: 60, step: 1, unit: '', description: '响应速度' },
  { name: 'Roll I', value: 80, min: 50, max: 120, step: 5, unit: '', description: '消除漂移' },
  { name: 'Roll D', value: 35, min: 20, max: 50, step: 1, unit: '', description: '抑制振荡' },
  { name: 'Pitch P', value: 47, min: 30, max: 60, step: 1, unit: '', description: '俯仰响应' },
  { name: 'Pitch I', value: 85, min: 50, max: 120, step: 5, unit: '', description: '俯仰稳定' },
  { name: 'Pitch D', value: 38, min: 20, max: 50, step: 1, unit: '', description: '俯仰阻尼' },
];

const tuningKnowledge = {
  symptoms: {
    sensitive: {
      keywords: ['灵敏', '太灵敏', '快', '太快', '响应快', '敏感', 'sensitive', 'fast', 'responsive'],
      cause: 'P值过高',
      solution: [
        { param: 'Roll P', action: 'decrease', amount: 2, reason: '降低响应速度' },
        { param: 'Pitch P', action: 'decrease', amount: 2, reason: '降低俯仰响应' },
      ]
    },
    unstable: {
      keywords: ['稳定', '抖', '振动', '晃动', '晃', 'unstable', 'vibration', 'shaky', 'oscillation'],
      cause: 'P过高或D不足',
      solution: [
        { param: 'Roll P', action: 'decrease', amount: 2, reason: '减少振荡' },
        { param: 'Roll D', action: 'increase', amount: 3, reason: '增加阻尼' },
        { param: 'Pitch D', action: 'increase', amount: 3, reason: '增加俯仰阻尼' },
      ]
    },
    drift: {
      keywords: ['漂移', '偏', '跑偏', 'drift', 'drifting', 'deviation'],
      cause: 'I值过低',
      solution: [
        { param: 'Roll I', action: 'increase', amount: 5, reason: '消除漂移' },
        { param: 'Pitch I', action: 'increase', amount: 5, reason: '消除俯仰漂移' },
      ]
    },
    slow: {
      keywords: ['慢', '迟钝', '反应慢', '跟不上', 'slow', 'lag', 'sluggish'],
      cause: 'P值过低',
      solution: [
        { param: 'Roll P', action: 'increase', amount: 3, reason: '提高响应速度' },
        { param: 'Pitch P', action: 'increase', amount: 3, reason: '提高俯仰响应' },
      ]
    },
    bounce: {
      keywords: ['弹跳', '回弹', 'bounce', 'rebound', 'overshoot'],
      cause: 'D值过低',
      solution: [
        { param: 'Roll D', action: 'increase', amount: 3, reason: '减少落地回弹' },
        { param: 'Pitch D', action: 'increase', amount: 3, reason: '减少俯仰回弹' },
      ]
    },
  },
  presets: {
    racing: {
      keywords: ['竞速', '比赛', 'racing', 'race', 'speed'],
      description: '🏁 竞速配置 - 追求极致响应',
      adjustments: [
        { param: 'Roll P', value: 48 },
        { param: 'Pitch P', value: 50 },
        { param: 'Roll D', value: 37 },
        { param: 'Pitch D', value: 40 },
      ]
    },
    freestyle: {
      keywords: ['花飞', 'freestyle', '自由飞'],
      description: '🎨 花飞配置 - 平滑流畅',
      adjustments: [
        { param: 'Roll P', value: 45 },
        { param: 'Pitch P', value: 47 },
        { param: 'Roll D', value: 35 },
        { param: 'Pitch D', value: 38 },
      ]
    },
    heavy: {
      keywords: ['重', '载重', 'heavy', 'load', '长续航', '航拍'],
      description: '📷 载重配置 - 稳定可靠',
      adjustments: [
        { param: 'Roll P', value: 42 },
        { param: 'Pitch P', value: 44 },
        { param: 'Roll D', value: 32 },
        { param: 'Pitch D', value: 35 },
      ]
    }
  }
};

const quickResponses = [
  { label: '太灵敏了', value: '飞机太灵敏了，我想让它慢一点' },
  { label: '有点抖动', value: '高速飞行时有点抖动' },
  { label: '想要更稳', value: '我想让飞行更稳定一些' },
  { label: '响应太慢', value: '感觉响应有点慢' },
];

export default function Home() {
  const [isConnected, setIsConnected] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisDone, setAnalysisDone] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [params, setParams] = useState<DroneParam[]>(initialParams);
  const [appliedSuggestions, setAppliedSuggestions] = useState<{ param: string; change: string }[]>([]);
  const [isAITyping, setIsAITyping] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [usbConnectedPort, setUsbConnectedPort] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { user, logout } = useAuth();
  const { connectedPort, connectToPort, disconnectFromPort } = useUSBSerial();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isAITyping]);

  const handleConnect = () => {
    if (!user) {
      setAuthModalOpen(true);
      return;
    }
    // 如果USB已连接，通过USB断开
    if (usbConnectedPort) {
      handleUSBDisconnect();
    } else {
      // 否则使用模拟连接
      setIsConnected(!isConnected);
      if (!isConnected) {
        setTimeout(() => {
          setIsAnalyzing(true);
          setTimeout(() => {
            setIsAnalyzing(false);
            setAnalysisDone(true);
            setMessages([{
              id: 1,
              content: '✈️ 无人机已连接（模拟模式）！现在可以告诉我您的飞行感受，我会帮您调参。试试点击下方的快捷选项，或直接输入描述。\n\n💡 提示：点击左下角"连接USB"按钮可以连接真实无人机。',
              isUser: false,
              timestamp: new Date(),
            }]);
          }, 2000);
        }, 500);
      } else {
        setAnalysisDone(false);
        setMessages([]);
        setParams(initialParams);
        setAppliedSuggestions([]);
      }
    }
  };

  const handleSend = (text?: string) => {
    const content = text || inputValue;
    if (!content.trim()) return;

    const userMsg: Message = {
      id: messages.length + 1,
      content: content,
      isUser: true,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');

    setIsAITyping(true);
    simulateAIResponse(content);
  };

  const findMatchingPattern = (input: string): { type: string; data: any } | null => {
    const lowerInput = input.toLowerCase();
    
    for (const [patternName, pattern] of Object.entries(tuningKnowledge.symptoms)) {
      for (const keyword of pattern.keywords) {
        if (lowerInput.includes(keyword.toLowerCase())) {
          return { type: 'symptom', data: pattern };
        }
      }
    }

    for (const [presetName, preset] of Object.entries(tuningKnowledge.presets)) {
      for (const keyword of preset.keywords) {
        if (lowerInput.includes(keyword.toLowerCase())) {
          return { type: 'preset', data: preset };
        }
      }
    }

    return null;
  };

  const simulateAIResponse = (userInput: string) => {
    setTimeout(() => {
      const match = findMatchingPattern(userInput);
      let responseContent = '';
      let adjustments: any[] = [];

      if (match?.type === 'symptom') {
        const symptom = match.data;
        responseContent = `🤔 分析中...发现问题：**${symptom.cause}**\n\n✅ 我来帮您调整这些参数：\n\n`;
        
        adjustments = symptom.solution;
        adjustments.forEach((sol, idx) => {
          responseContent += `${idx + 1}. ${sol.param}: ${sol.action === 'increase' ? '增加' : '降低'} ${sol.amount} (${sol.reason})\n`;
        });
        responseContent += '\n✨ 参数已自动调整完成！';
      } else if (match?.type === 'preset') {
        const preset = match.data;
        responseContent = `${preset.description}\n\n⚙️ 已为您应用这个配置：\n\n`;
        
        adjustments = preset.adjustments;
        adjustments.forEach(adj => {
          responseContent += `• ${adj.param}: ${adj.value}\n`;
        });
        responseContent += '\n✨ 预设已应用！';
      } else {
        responseContent = '我理解您的描述！为了更好地帮您调参，您可以试试这些描述方式：\n\n';
        responseContent += '• "太灵敏了"\n';
        responseContent += '• "有点抖动"\n';
        responseContent += '• "想要更稳"\n';
        responseContent += '• "竞速配置"\n\n';
        responseContent += '或者直接点击下方的快捷选项！';
      }

      const responseMsg: Message = {
        id: messages.length + 2,
        content: responseContent,
        isUser: false,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, responseMsg]);
      setIsAITyping(false);

      if (adjustments.length > 0) {
        applyAdjustments(adjustments);
      }
    }, 1500);
  };

  const applyAdjustments = (adjustments: any[]) => {
    if (adjustments[0]?.hasOwnProperty('action')) {
      const symptomAdjustments = adjustments as { param: string; action: string; amount: number; reason: string }[];
      setParams(prev => prev.map(p => {
        const adj = symptomAdjustments.find(a => a.param === p.name);
        if (adj) {
          const newValue = adj.action === 'increase' 
            ? Math.min(p.max, p.value + adj.amount)
            : Math.max(p.min, p.value - adj.amount);
          return { ...p, value: newValue };
        }
        return p;
      }));
      setAppliedSuggestions(symptomAdjustments.map(a => ({
        param: a.param,
        change: `${a.action === 'increase' ? '↑' : '↓'} ${a.amount}`
      })));
    } else {
      const presetAdjustments = adjustments as { param: string; value: number }[];
      setParams(prev => prev.map(p => {
        const adj = presetAdjustments.find(a => a.param === p.name);
        if (adj) {
          return { ...p, value: adj.value };
        }
        return p;
      }));
      setAppliedSuggestions(presetAdjustments.map(a => ({
        param: a.param,
        change: `→ ${a.value}`
      })));
    }
  };

  const handleParamChange = (name: string, value: number) => {
    setParams(prev => prev.map(p => p.name === name ? { ...p, value } : p));
    setAppliedSuggestions(prev => prev.filter(s => s.param !== name));
  };

  const handleApplyParams = () => {
    if (!user) {
      setAuthModalOpen(true);
      return;
    }
    setMessages(prev => [...prev, {
      id: prev.length + 1,
      content: '🚀 参数已发送到无人机！现在可以试飞一下，看看效果如何。如果还需要调整，继续告诉我就行！',
      isUser: false,
      timestamp: new Date(),
    }]);
  };

  const handleResetParams = () => {
    setParams(initialParams);
    setAppliedSuggestions([]);
    setMessages(prev => [...prev, {
      id: prev.length + 1,
      content: '🔄 参数已重置为默认值',
      isUser: false,
      timestamp: new Date(),
    }]);
  };

  const handleUSBConnect = (port: string) => {
    setUsbConnectedPort(port);
    setIsConnected(true);
    setTimeout(() => {
      setIsAnalyzing(true);
      setTimeout(() => {
        setIsAnalyzing(false);
        setAnalysisDone(true);
        setMessages([{
          id: 1,
          content: `✈️ 无人机已通过USB连接 (${port})！现在可以告诉我您的飞行感受，我会帮您调参。试试点击下方的快捷选项，或直接输入描述。`,
          isUser: false,
          timestamp: new Date(),
        }]);
      }, 2000);
    }, 500);
  };

  const handleUSBDisconnect = () => {
    setUsbConnectedPort(null);
    setIsConnected(false);
    setAnalysisDone(false);
    setMessages([]);
    setParams(initialParams);
    setAppliedSuggestions([]);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-900/80 backdrop-blur-xl border-b border-gray-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-cyan-400 to-purple-500 flex items-center justify-center shadow-lg shadow-cyan-500/30">
                <span className="text-2xl">🎯</span>
              </div>
              <div>
                <h1 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
                  HKAIC 智能调参助手
                </h1>
                <p className="text-sm text-gray-400">调参，从未如此简单</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              {user ? (
                <div className="flex items-center gap-4">
                  <span className="text-sm text-gray-400">
                    {user.username || user.email}
                  </span>
                  <button
                    onClick={logout}
                    className="px-4 py-2 rounded-xl bg-gray-800 hover:bg-gray-700 transition text-sm"
                  >
                    退出
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setAuthModalOpen(true)}
                  className="px-6 py-2 rounded-xl bg-gradient-to-r from-cyan-400 to-purple-500 hover:opacity-90 transition font-semibold"
                >
                  登录 / 注册
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!isConnected && !analysisDone ? (
          /* Welcome Screen */
          <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
            <div className="w-32 h-32 rounded-3xl bg-gradient-to-br from-cyan-400 to-purple-500 flex items-center justify-center shadow-2xl shadow-cyan-500/30 mb-8">
              <span className="text-5xl">✈️</span>
            </div>
            <h2 className="text-4xl font-bold mb-4 bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
              简单三步，完美调参
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8 mb-12 max-w-3xl">
              <div className="bg-gray-800/50 rounded-2xl p-6 border border-gray-700">
                <div className="w-12 h-12 bg-cyan-500/20 rounded-xl flex items-center justify-center mb-4 mx-auto">
                  <span className="text-2xl">1️⃣</span>
                </div>
                <h3 className="font-semibold mb-2">连接无人机</h3>
                <p className="text-sm text-gray-400">点击右上角按钮连接您的无人机</p>
              </div>
              <div className="bg-gray-800/50 rounded-2xl p-6 border border-gray-700">
                <div className="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center mb-4 mx-auto">
                  <span className="text-2xl">2️⃣</span>
                </div>
                <h3 className="font-semibold mb-2">描述飞行感受</h3>
                <p className="text-sm text-gray-400">用自然语言告诉AI您的飞行体验</p>
              </div>
              <div className="bg-gray-800/50 rounded-2xl p-6 border border-gray-700">
                <div className="w-12 h-12 bg-green-500/20 rounded-xl flex items-center justify-center mb-4 mx-auto">
                  <span className="text-2xl">3️⃣</span>
                </div>
                <h3 className="font-semibold mb-2">应用优化参数</h3>
                <p className="text-sm text-gray-400">AI自动调整，一键应用到无人机</p>
              </div>
            </div>
            
            <button
              onClick={handleConnect}
              disabled={!user && !authModalOpen}
              className="px-8 py-4 rounded-2xl text-lg font-semibold bg-gradient-to-r from-cyan-400 to-purple-500 hover:opacity-90 transition shadow-lg shadow-cyan-500/30"
            >
              {user ? '连接无人机' : '登录后开始'}
            </button>
          </div>
        ) : (
          /* Main Interface */
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column */}
            <div className="lg:col-span-1 space-y-6">
              {/* Connection Panel */}
              <div className="bg-gray-800/50 rounded-2xl border border-gray-700 p-6">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <span className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`} />
                  {isConnected ? '已连接' : '未连接'}
                </h3>
                <button
                  onClick={handleConnect}
                  className={`w-full py-3 rounded-xl font-semibold transition flex items-center justify-center gap-2 ${
                    isConnected 
                      ? 'bg-red-500/20 text-red-400 border border-red-500/50 hover:bg-red-500/30' 
                      : 'bg-gradient-to-r from-cyan-400 to-purple-500 hover:opacity-90'
                  }`}
                >
                  {isAnalyzing ? (
                    <>
                      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      连接中...
                    </>
                  ) : (
                    <>{isConnected ? '断开连接' : '连接无人机'}</>
                  )}
                </button>
              </div>
              
              {/* Quick Tips */}
              <div className="p-6 bg-gray-800/30 rounded-2xl border border-gray-700">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <span>📚</span>
                  调参小贴士
                </h3>
                <div className="space-y-3">
                  <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl">
                    <h4 className="font-semibold text-red-400 mb-1 text-sm">P值过高</h4>
                    <p className="text-xs text-gray-400">振荡、抖动</p>
                    <p className="text-xs text-gray-500 mt-1">降低P值</p>
                  </div>
                  <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-xl">
                    <h4 className="font-semibold text-yellow-400 mb-1 text-sm">I值过低</h4>
                    <p className="text-xs text-gray-400">漂移、偏航</p>
                    <p className="text-xs text-gray-500 mt-1">增加I值</p>
                  </div>
                  <div className="p-3 bg-purple-500/10 border border-purple-500/30 rounded-xl">
                    <h4 className="font-semibold text-purple-400 mb-1 text-sm">D值不当</h4>
                    <p className="text-xs text-gray-400">回弹、响应慢</p>
                    <p className="text-xs text-gray-500 mt-1">根据情况调整</p>
                  </div>
                </div>
              </div>
              
              {/* Supported Models */}
              <div className="p-6 bg-gray-800/30 rounded-2xl border border-gray-700">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <span>🎮</span>
                  支持的飞控
                </h3>
                <div className="space-y-3">
                  <div className="p-3 bg-cyan-500/10 border border-cyan-500/30 rounded-xl">
                    <h4 className="font-semibold text-cyan-400 mb-1 text-sm">PX4 (推荐)</h4>
                    <p className="text-xs text-gray-400">Pixhawk, Cube系列</p>
                    <p className="text-xs text-gray-500 mt-1">适合航拍、VTOL</p>
                  </div>
                  <div className="p-3 bg-purple-500/10 border border-purple-500/30 rounded-xl">
                    <h4 className="font-semibold text-purple-400 mb-1 text-sm">Betaflight</h4>
                    <p className="text-xs text-gray-400">F4/F7/H7系列飞控</p>
                    <p className="text-xs text-gray-500 mt-1">适合穿越机、花飞</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Chat Panel */}
            <div className="lg:col-span-1 bg-gray-800/50 rounded-2xl border border-gray-700 overflow-hidden flex flex-col h-[650px]">
              <div className="p-6 border-b border-gray-700 bg-gradient-to-r from-gray-800 to-gray-900">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <span className="text-cyan-400">🤖</span>
                  AI 调参助手
                </h3>
              </div>
              
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {messages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-full text-gray-500">
                    <div className="text-5xl mb-4">🎯</div>
                    <p className="text-lg mb-2">准备好开始调参了！</p>
                    <p className="text-sm">告诉我您的飞行感受，我会帮您优化</p>
                  </div>
                ) : (
                  <>
                    {messages.map(msg => (
                      <div
                        key={msg.id}
                        className={`flex gap-3 ${msg.isUser ? 'justify-end' : 'justify-start'}`}
                      >
                        {!msg.isUser && <span className="text-3xl">🤖</span>}
                        <div className={`max-w-[85%] p-5 rounded-2xl ${
                          msg.isUser 
                            ? 'bg-gradient-to-r from-cyan-500 to-purple-500 rounded-br-sm' 
                            : 'bg-gray-700/80 rounded-bl-sm'
                        }`}>
                          <p className="text-sm whitespace-pre-wrap font-mono leading-relaxed">{msg.content}</p>
                        </div>
                        {msg.isUser && <span className="text-3xl">👤</span>}
                      </div>
                    ))}
                    {isAITyping && (
                      <div className="flex gap-3 justify-start">
                        <span className="text-3xl">🤖</span>
                        <div className="bg-gray-700/80 rounded-2xl p-5 rounded-bl-sm">
                          <div className="flex gap-2">
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                            <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                          </div>
                        </div>
                      </div>
                    )}
                  </>
                )}
                <div ref={messagesEndRef} />
              </div>
              
              {/* Quick Responses */}
              {analysisDone && messages.length > 0 && (
                <div className="px-6 pb-4">
                  <div className="flex flex-wrap gap-2">
                    {quickResponses.map((qr, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleSend(qr.value)}
                        disabled={isAITyping}
                        className="px-4 py-2 text-sm bg-gray-700/80 hover:bg-gray-600 rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed border border-gray-600"
                      >
                        {qr.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Input */}
              <div className="p-6 border-t border-gray-700 bg-gray-900/50">
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="描述您的飞行感受，比如：飞机太灵敏了..."
                    disabled={!analysisDone || isAITyping}
                    className="flex-1 px-5 py-4 rounded-xl bg-gray-700 border border-gray-600 focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20 disabled:bg-gray-800 disabled:text-gray-500 outline-none text-sm transition-all"
                  />
                  <button
                    onClick={() => handleSend()}
                    disabled={!analysisDone || !inputValue.trim() || isAITyping}
                    className={`px-6 py-4 rounded-xl font-semibold transition-all ${
                      !analysisDone || !inputValue.trim() || isAITyping
                        ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                        : 'bg-gradient-to-r from-cyan-400 to-purple-500 hover:opacity-90 shadow-lg shadow-cyan-500/30'
                    }`}
                  >
                    发送
                  </button>
                </div>
              </div>
            </div>

            {/* Params Panel */}
            <div className="lg:col-span-1 bg-gray-800/50 rounded-2xl border border-gray-700 p-6 flex flex-col h-[650px]">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <span className="text-purple-400">⚙️</span>
                  PID 参数
                </h3>
                <div className="flex gap-2">
                  <button
                    onClick={handleResetParams}
                    className="px-3 py-2 text-sm rounded-xl bg-gray-700 hover:bg-gray-600 transition-colors"
                  >
                    重置
                  </button>
                  <button
                    onClick={handleApplyParams}
                    disabled={!isConnected || messages.length < 2}
                    className={`px-4 py-2 text-sm rounded-xl font-semibold transition-all ${
                      !isConnected || messages.length < 2
                        ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                        : 'bg-gradient-to-r from-green-500 to-cyan-500 hover:opacity-90 shadow-lg shadow-green-500/30'
                    }`}
                  >
                    应用
                  </button>
                </div>
              </div>
              
              <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                {params.map((param, idx) => {
                  const applied = appliedSuggestions.find(s => s.param === param.name);
                  return (
                    <div key={idx} className={`p-5 rounded-2xl border transition-all ${
                      applied 
                        ? 'bg-cyan-500/10 border-cyan-500/30' 
                        : 'bg-gray-700/50 border-gray-600'
                    }`}>
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <label className="font-semibold text-sm flex items-center gap-2">
                            {param.name}
                            {applied && (
                              <span className="px-2 py-1 bg-cyan-500/20 text-cyan-400 text-xs rounded-full font-bold">
                                {applied.change}
                              </span>
                            )}
                          </label>
                          <p className="text-xs text-gray-400 mt-1">{param.description}</p>
                        </div>
                        <span className="text-cyan-400 font-mono font-bold text-xl">
                          {param.value}
                        </span>
                      </div>
                      <input
                        type="range"
                        min={param.min}
                        max={param.max}
                        step={param.step}
                        value={param.value}
                        onChange={(e) => handleParamChange(param.name, parseFloat(e.target.value))}
                        className="w-full h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer accent-cyan-400 hover:accent-cyan-300 transition-all"
                      />
                      <div className="flex justify-between text-xs text-gray-500 mt-2">
                        <span>{param.min}</span>
                        <span>{param.max}</span>
                      </div>
                    </div>
                  );
                })}
              </div>

              {appliedSuggestions.length > 0 && (
                <div className="mt-6 p-4 bg-gradient-to-r from-cyan-500/10 to-purple-500/10 border border-cyan-500/30 rounded-2xl">
                  <p className="text-cyan-400 text-sm font-semibold flex items-center gap-2">
                    <span>✨</span>
                    参数已优化！点击"应用"发送到无人机
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 bg-gray-900/50 py-8 mt-12">
        <div className="max-w-6xl mx-auto px-4 text-center text-gray-500 text-sm">
          <p className="text-lg mb-2">🎯 调参，从未如此简单</p>
          <p className="text-xs opacity-60">基于 PX4 & Betaflight 开源调参知识</p>
        </div>
      </footer>

      {/* Auth Modal */}
      <AuthModal isOpen={authModalOpen} onClose={() => setAuthModalOpen(false)} />
      
      {/* USB Connection Panel */}
      <USBConnectionPanel
        onConnect={handleUSBConnect}
        onDisconnect={handleUSBDisconnect}
        connectedPort={usbConnectedPort}
      />
    </div>
  );
}
