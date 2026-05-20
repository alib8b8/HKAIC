"use client";

import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Upload as UploadIcon,
  FileText,
  X,
  CheckCircle2,
  Loader2,
  Zap,
} from "lucide-react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";

const UploadZone = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [format, setFormat] = useState<string>('DJI');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const router = useRouter();
  
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
  
  const handleDragLeave = () => {
    setIsDragging(false);
  };
  
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
    }
  };
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
    }
  };
  
  const handleUpload = () => {
    if (!file) return;
    
    setUploading(true);
    setUploadProgress(0);
    
    const interval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(() => {
            router.push('/report/1');
          }, 500);
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  };
  
  const removeFile = () => {
    setFile(null);
    setUploading(false);
    setUploadProgress(0);
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload Flight Log</CardTitle>
        <p className="text-text-secondary text-sm mt-2">
          Drag and drop your flight log file, or click to browse
        </p>
      </CardHeader>
      <CardContent>
        {!file ? (
          <div
            className={`border-2 border-dashed rounded-2xl p-12 text-center transition-all cursor-pointer ${
              isDragging 
                ? 'border-primary bg-primary/5' 
                : 'border-border hover:border-primary/50'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-input')?.click()}
          >
            <input
              id="file-input"
              type="file"
              className="hidden"
              onChange={handleFileChange}
              accept=".log,.bin,.ulg,.txt"
            />
            <motion.div
              animate={isDragging ? { scale: 1.05 } : { scale: 1 }}
              transition={{ duration: 0.2 }}
            >
              <div className="w-20 h-20 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-6">
                <UploadIcon className="w-10 h-10 text-primary" />
              </div>
              <p className="text-lg font-medium mb-2">Drop your flight log here</p>
              <p className="text-text-muted mb-6">Supports .log, .bin, .ulg, .txt files</p>
              <Button variant="outline">Browse Files</Button>
            </motion.div>
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex items-center justify-between p-6 rounded-2xl bg-background-secondary">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                  <FileText className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <p className="font-medium">{file.name}</p>
                  <p className="text-sm text-text-muted">{(file.size / 1024).toFixed(2)} KB</p>
                </div>
              </div>
              {!uploading && (
                <button
                  onClick={removeFile}
                  className="text-text-muted hover:text-text-primary transition"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>
            
            <div className="space-y-4">
              <label className="block">
                <span className="text-text-secondary text-sm font-medium">Flight Controller Format</span>
                <div className="flex flex-wrap gap-3 mt-2">
                  {['DJI', 'PX4', 'Betaflight', 'Ardupilot', 'INAV'].map((f) => (
                    <button
                      key={f}
                      onClick={() => setFormat(f)}
                      className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                        format === f
                          ? 'bg-primary text-white'
                          : 'bg-surface border border-border text-text-secondary hover:border-primary/50'
                      }`}
                    >
                      {f}
                    </button>
                  ))}
                </div>
              </label>
            </div>
            
            {uploading && (
              <div className="space-y-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-text-secondary">Processing...</span>
                  <span className="font-medium text-primary">{uploadProgress}%</span>
                </div>
                <div className="h-2 bg-background-secondary rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-primary to-secondary"
                    initial={{ width: 0 }}
                    animate={{ width: `${uploadProgress}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
                <div className="flex items-center gap-2 text-sm text-text-muted">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>AI is analyzing your flight data...</span>
                </div>
              </div>
            )}
            
            {!uploading && (
              <div className="flex gap-4">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={removeFile}
                >
                  Cancel
                </Button>
                <Button
                  className="flex-1 btn-glow"
                  onClick={handleUpload}
                >
                  <Zap className="w-5 h-5 mr-2" />
                  Analyze Log
                </Button>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export { UploadZone };
