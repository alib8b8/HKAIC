// 用户调参数据备份服务

export interface ParamSnapshot {
  timestamp: Date;
  params: Record<string, number>;
  description?: string;
}

export interface TuningSession {
  sessionId: string;
  startTime: Date;
  endTime?: Date;
  snapshots: ParamSnapshot[];
  conversations: {
    role: 'user' | 'ai';
    content: string;
    timestamp: Date;
  }[];
}

export interface UserBackup {
  version: string;
  exportTime: Date;
  userEmail?: string;
  sessions: TuningSession[];
  currentParams: Record<string, number>;
  presets: Record<string, Record<string, number>>;
  preferences: {
    theme: 'dark' | 'light';
    language: 'zh' | 'en';
  };
}

class BackupService {
  private readonly STORAGE_KEY = 'hkaic_tuning_data';
  private sessions: TuningSession[] = [];
  private currentSession: TuningSession | null = null;

  constructor() {
    this.loadFromStorage();
  }

  private loadFromStorage() {
    if (typeof window === 'undefined') return;
    
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (stored) {
        const data = JSON.parse(stored);
        this.sessions = data.sessions || [];
      }
    } catch (error) {
      console.error('Failed to load tuning data:', error);
    }
  }

  private saveToStorage() {
    if (typeof window === 'undefined') return;
    
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify({
        sessions: this.sessions,
        lastUpdated: new Date().toISOString()
      }));
    } catch (error) {
      console.error('Failed to save tuning data:', error);
    }
  }

  startSession(): string {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    this.currentSession = {
      sessionId,
      startTime: new Date(),
      snapshots: [],
      conversations: []
    };
    return sessionId;
  }

  addSnapshot(params: Record<string, number>, description?: string) {
    if (!this.currentSession) {
      this.startSession();
    }

    const snapshot: ParamSnapshot = {
      timestamp: new Date(),
      params: { ...params },
      description
    };

    this.currentSession!.snapshots.push(snapshot);
    this.saveToStorage();
  }

  addConversation(role: 'user' | 'ai', content: string) {
    if (!this.currentSession) {
      this.startSession();
    }

    this.currentSession!.conversations.push({
      role,
      content,
      timestamp: new Date()
    });
    this.saveToStorage();
  }

  endSession() {
    if (this.currentSession) {
      this.currentSession.endTime = new Date();
      this.sessions.push(this.currentSession);
      this.currentSession = null;
      this.saveToStorage();
    }
  }

  exportBackup(currentParams: Record<string, number>, presets: Record<string, Record<string, number>>, userEmail?: string): UserBackup {
    return {
      version: '1.0.0',
      exportTime: new Date(),
      userEmail,
      sessions: this.sessions,
      currentParams,
      presets,
      preferences: {
        theme: 'dark',
        language: 'zh'
      }
    };
  }

  downloadBackup(backup: UserBackup, filename?: string) {
    const dataStr = JSON.stringify(backup, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || `hkaic_backup_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  async importBackup(file: File): Promise<UserBackup> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        try {
          const backup = JSON.parse(e.target?.result as string) as UserBackup;
          
          if (!backup.version || !backup.currentParams) {
            throw new Error('Invalid backup file format');
          }

          this.sessions = backup.sessions || [];
          this.saveToStorage();
          
          resolve(backup);
        } catch (error) {
          reject(new Error('Failed to parse backup file'));
        }
      };
      
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  }

  clearAllData() {
    this.sessions = [];
    this.currentSession = null;
    if (typeof window !== 'undefined') {
      localStorage.removeItem(this.STORAGE_KEY);
    }
  }

  getSessions(): TuningSession[] {
    return this.sessions;
  }

  exportAsCSV(currentParams: Record<string, number>): string {
    const headers = ['Parameter', 'Value', 'Timestamp'];
    const rows = Object.entries(currentParams).map(([param, value]) => [
      param,
      value.toString(),
      new Date().toISOString()
    ]);
    
    return [headers, ...rows].map(row => row.join(',')).join('\n');
  }

  downloadCSV(currentParams: Record<string, number>, filename?: string) {
    const csv = this.exportAsCSV(currentParams);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || `hkaic_params_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }
}

export const backupService = new BackupService();
