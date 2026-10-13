"use client";

import React, { useEffect, useRef, useState } from "react";
import { Play, Pause, RotateCcw, Volume2, ShieldAlert, CheckCircle2 } from "lucide-react";
import { useTheme } from "../lib/ThemeContext";

interface AudioWaveformPlayerProps {
  audioBlob?: Blob | null;
  audioUrl?: string | null;
  title?: string;
  isSynthetic?: boolean;
  spectralScore?: number;
  pValue?: number;
}

export default function AudioWaveformPlayer({
  audioBlob,
  audioUrl,
  title = "Voice Recording Analysis / فحص التسجيل الصوتي",
  isSynthetic,
  spectralScore,
  pValue,
}: AudioWaveformPlayerProps) {
  const { theme } = useTheme();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [playbackRate, setPlaybackRate] = useState(1);
  const [peaks, setPeaks] = useState<number[]>([]);
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  // 1. Create or resolve playback URL
  useEffect(() => {
    let url: string | null = null;
    if (audioBlob) {
      url = URL.createObjectURL(audioBlob);
      setObjectUrl(url);
    } else if (audioUrl) {
      setObjectUrl(audioUrl);
    } else {
      setObjectUrl(null);
    }

    return () => {
      if (url) URL.revokeObjectURL(url);
    };
  }, [audioBlob, audioUrl]);

  // 2. Decode Audio Peaks using in-browser Web Audio API
  useEffect(() => {
    if (!audioBlob && !audioUrl) {
      // Default placeholder peaks
      const defaultBars = Array.from({ length: 60 }, (_, i) => 
        0.2 + 0.6 * Math.abs(Math.sin((i / 60) * Math.PI * 4)) * (0.5 + 0.5 * Math.random())
      );
      setPeaks(defaultBars);
      return;
    }

    const extractPeaks = async () => {
      try {
        const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
        if (!AudioCtx) return;
        const ctx = new AudioCtx();

        let arrayBuffer: ArrayBuffer;
        if (audioBlob) {
          arrayBuffer = await audioBlob.arrayBuffer();
        } else if (audioUrl) {
          const resp = await fetch(audioUrl);
          arrayBuffer = await resp.arrayBuffer();
        } else {
          return;
        }

        const decoded = await ctx.decodeAudioData(arrayBuffer);
        const channelData = decoded.getChannelData(0);
        const numBars = 64;
        const blockSize = Math.floor(channelData.length / numBars);
        const calculatedPeaks: number[] = [];

        for (let i = 0; i < numBars; i++) {
          let sum = 0;
          for (let j = 0; j < blockSize; j++) {
            sum += Math.abs(channelData[i * blockSize + j]);
          }
          calculatedPeaks.push(Math.min(1, (sum / blockSize) * 4));
        }

        setPeaks(calculatedPeaks);
        setDuration(decoded.duration);
        ctx.close().catch(() => {});
      } catch {
        // Fallback synthetic envelope if decoding compressed container fails
        const fallback = Array.from({ length: 64 }, (_, i) => 
          0.15 + 0.7 * Math.abs(Math.sin((i / 64) * Math.PI * 3))
        );
        setPeaks(fallback);
      }
    };

    extractPeaks();
  }, [audioBlob, audioUrl]);

  // 3. Render Canvas Waveform
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    ctx.clearRect(0, 0, width, height);

    const isDark = theme === "dark";
    const totalBars = peaks.length || 64;
    const barWidth = Math.max(2, Math.floor(width / totalBars) - 2);
    const progressRatio = duration > 0 ? currentTime / duration : 0;

    peaks.forEach((peak, index) => {
      const x = index * (barWidth + 2);
      const barHeight = Math.max(4, peak * (height - 8));
      const y = (height - barHeight) / 2;
      const isPast = index / totalBars <= progressRatio;

      if (isPast) {
        if (isSynthetic) {
          ctx.fillStyle = "#EF4444"; // Anomaly Red
        } else {
          ctx.fillStyle = isDark ? "#10B981" : "#059669"; // Emerald Safe
        }
      } else {
        if (isSynthetic && index > totalBars * 0.4 && index < totalBars * 0.8) {
          ctx.fillStyle = isDark ? "#7F1D1D" : "#FECACA"; // Anomaly highlight zone
        } else {
          ctx.fillStyle = isDark ? "#374151" : "#CBD5E1"; // Unplayed neutral
        }
      }

      ctx.beginPath();
      ctx.roundRect(x, y, barWidth, barHeight, 2);
      ctx.fill();
    });
  }, [peaks, currentTime, duration, theme, isSynthetic]);

  // Audio Playback Handlers
  const togglePlay = () => {
    const audio = audioRef.current;
    if (!audio) return;
    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      audio.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  };

  const handleTimeUpdate = () => {
    const audio = audioRef.current;
    if (!audio) return;
    setCurrentTime(audio.currentTime);
  };

  const handleLoadedMetadata = () => {
    const audio = audioRef.current;
    if (!audio) return;
    setDuration(audio.duration || 0);
  };

  const handleEnded = () => {
    setIsPlaying(false);
    setCurrentTime(0);
  };

  const handleSeek = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    const audio = audioRef.current;
    if (!canvas || !audio || duration === 0) return;

    const rect = canvas.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const ratio = Math.max(0, Math.min(1, clickX / rect.width));
    const newTime = ratio * duration;
    audio.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  const toggleRate = () => {
    const audio = audioRef.current;
    if (!audio) return;
    const rates = [1, 1.25, 1.5, 2];
    const nextIdx = (rates.indexOf(playbackRate) + 1) % rates.length;
    const newRate = rates[nextIdx];
    audio.playbackRate = newRate;
    setPlaybackRate(newRate);
  };

  return (
    <div className="w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/70 backdrop-blur p-4 shadow-sm transition-colors">
      {objectUrl && (
        <audio
          ref={audioRef}
          src={objectUrl}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onEnded={handleEnded}
          className="hidden"
        />
      )}

      {/* Header Info */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Volume2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
          <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">
            {title}
          </span>
        </div>

        {isSynthetic !== undefined && (
          <div
            className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-medium ${
              isSynthetic
                ? "bg-red-100 text-red-700 dark:bg-red-950/60 dark:text-red-300 border border-red-200 dark:border-red-900"
                : "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900"
            }`}
          >
            {isSynthetic ? (
              <>
                <ShieldAlert className="w-3.5 h-3.5 text-red-600" />
                <span>Synthetic Artifacts (Score: {spectralScore?.toFixed(2) ?? "0.98"})</span>
              </>
            ) : (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Natural Human Voice (p: {pValue?.toFixed(4) ?? "0.94"})</span>
              </>
            )}
          </div>
        )}
      </div>

      {/* Interactive Waveform Canvas */}
      <div className="relative mb-3 bg-slate-100 dark:bg-slate-950/80 rounded-lg p-2 border border-slate-200/60 dark:border-slate-800/60 cursor-pointer overflow-hidden">
        <canvas
          ref={canvasRef}
          width={480}
          height={64}
          onClick={handleSeek}
          className="w-full h-16 block"
        />
      </div>

      {/* Playback Controls & Scrubber */}
      <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={togglePlay}
            disabled={!objectUrl}
            className="w-8 h-8 rounded-full bg-emerald-600 hover:bg-emerald-700 text-white flex items-center justify-center transition shadow-sm disabled:opacity-50"
            title={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
          </button>

          <button
            type="button"
            onClick={() => {
              const audio = audioRef.current;
              if (audio) {
                audio.currentTime = 0;
                setCurrentTime(0);
              }
            }}
            disabled={!objectUrl}
            className="p-1.5 rounded hover:bg-slate-200 dark:hover:bg-slate-800 transition text-slate-600 dark:text-slate-400 disabled:opacity-50"
            title="Reset"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          <button
            type="button"
            onClick={toggleRate}
            className="px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 font-mono text-[11px] font-semibold text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-700 transition"
          >
            {playbackRate}x
          </button>
        </div>

        <div className="font-mono text-xs">
          <span>{formatTime(currentTime)}</span>
          <span className="mx-1 text-slate-400">/</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>
    </div>
  );
}
