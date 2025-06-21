# 🎨 Charlie Frontend Guidelines

## 📋 Overview

This document outlines the frontend development guidelines for Charlie across all platforms: Web (Next.js), Desktop (Electron), and CLI (Python Rich).

## 🌐 Web Application (Next.js 14)

### Project Structure
```
charlie-web/
├── app/                       # Next.js 14 App Router
│   ├── (auth)/
│   │   ├── login/
│   │   └── register/
│   ├── dashboard/
│   │   ├── page.tsx          # Main dashboard
│   │   ├── chat/             # Voice chat interface
│   │   ├── memory/           # Memory management
│   │   └── settings/         # User settings
│   ├── globals.css           # Global styles
│   ├── layout.tsx           # Root layout
│   └── page.tsx             # Landing page
├── components/
│   ├── ui/                  # shadcn/ui components
│   ├── voice/               # Voice-related components
│   ├── chat/                # Chat interface components
│   ├── layout/              # Layout components
│   └── forms/               # Form components
├── lib/
│   ├── supabase.ts          # Supabase client
│   ├── utils.ts             # Utility functions
│   └── voice.ts             # Voice processing utilities
├── hooks/
│   ├── use-voice.ts         # Voice interaction hook
│   ├── use-auth.ts          # Authentication hook
│   └── use-supabase.ts      # Supabase hook
├── stores/
│   ├── auth-store.ts        # Authentication state
│   ├── chat-store.ts        # Chat state
│   └── settings-store.ts    # Settings state
└── types/
    ├── auth.ts              # Authentication types
    ├── chat.ts              # Chat types
    └── api.ts               # API types
```

### Technology Stack
```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "typescript": "^5.2.0",
    "@supabase/supabase-js": "^2.38.0",
    "tailwindcss": "^3.3.0",
    "@radix-ui/react-dialog": "*",
    "@radix-ui/react-button": "*",
    "@radix-ui/react-avatar": "*",
    "zustand": "^4.4.0",
    "framer-motion": "^10.16.0",
    "lucide-react": "^0.294.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0"
  }
}
```

### Design System

#### Color Palette
```css
/* colors.css */
:root {
  /* Primary Colors - Arc Reactor Blue */
  --primary: 199 89% 48%;          /* #00b8d4 */
  --primary-foreground: 0 0% 98%;  /* #fafafa */
  
  /* Secondary Colors - Gold Accent */
  --secondary: 45 93% 47%;         /* #f39c12 */
  --secondary-foreground: 0 0% 9%; /* #171717 */
  
  /* Background Colors */
  --background: 0 0% 3.9%;         /* #0a0a0a */
  --foreground: 0 0% 98%;          /* #fafafa */
  
  /* Muted Colors */
  --muted: 0 0% 14.9%;            /* #262626 */
  --muted-foreground: 0 0% 63.9%; /* #a3a3a3 */
  
  /* Accent Colors */
  --accent: 0 0% 14.9%;           /* #262626 */
  --accent-foreground: 0 0% 98%;  /* #fafafa */
  
  /* Border Colors */
  --border: 0 0% 14.9%;           /* #262626 */
  --input: 0 0% 14.9%;            /* #262626 */
  
  /* Ring Colors */
  --ring: 199 89% 48%;            /* #00b8d4 */
}
```

#### Typography
```css
/* typography.css */
.font-mono {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

.font-sans {
  font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
}

/* Text Styles */
.text-gradient {
  @apply bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent;
}

.glow-text {
  text-shadow: 0 0 10px rgb(0 184 212 / 0.5);
}
```

### Component Architecture

#### Voice Interface Component
```tsx
// components/voice/voice-interface.tsx
'use client';

import { useState, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Mic, MicOff, Volume2 } from 'lucide-react';
import { useVoice } from '@/hooks/use-voice';
import { motion } from 'framer-motion';

export function VoiceInterface() {
  const { isListening, startListening, stopListening, speak } = useVoice();
  const [isThinking, setIsThinking] = useState(false);

  const handleVoiceCommand = useCallback(async () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  return (
    <div className="flex flex-col items-center space-y-4">
      <motion.div
        animate={{
          scale: isListening ? 1.1 : 1,
          boxShadow: isListening ? '0 0 20px rgb(0 184 212 / 0.5)' : 'none'
        }}
        transition={{ duration: 0.2 }}
      >
        <Button
          onClick={handleVoiceCommand}
          size="lg"
          className={`w-16 h-16 rounded-full ${
            isListening 
              ? 'bg-primary hover:bg-primary/90' 
              : 'bg-muted hover:bg-muted/90'
          }`}
        >
          {isListening ? (
            <MicOff className="w-6 h-6" />
          ) : (
            <Mic className="w-6 h-6" />
          )}
        </Button>
      </motion.div>
      
      <p className="text-sm text-muted-foreground">
        {isListening ? 'Listening...' : 'Click to speak with Charlie'}
      </p>
    </div>
  );
}
```

#### Chat Interface Component
```tsx
// components/chat/chat-interface.tsx
'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send } from 'lucide-react';
import { useChatStore } from '@/stores/chat-store';

export function ChatInterface() {
  const [input, setInput] = useState('');
  const { messages, sendMessage, isLoading } = useChatStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    
    await sendMessage(input);
    setInput('');
  };

  return (
    <div className="flex flex-col h-full">
      <ScrollArea ref={scrollRef} className="flex-1 p-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`mb-4 flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              {message.content}
            </div>
          </div>
        ))}
      </ScrollArea>
      
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex space-x-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            disabled={isLoading}
          />
          <Button type="submit" disabled={isLoading || !input.trim()}>
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </form>
    </div>
  );
}
```

### State Management (Zustand)

#### Authentication Store
```tsx
// stores/auth-store.ts
import { create } from 'zustand';
import { supabase } from '@/lib/supabase';

interface AuthState {
  user: any | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  initialize: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  loading: true,
  
  signIn: async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    
    if (error) throw error;
    set({ user: data.user });
  },
  
  signOut: async () => {
    await supabase.auth.signOut();
    set({ user: null });
  },
  
  initialize: async () => {
    const { data } = await supabase.auth.getSession();
    set({ user: data.session?.user || null, loading: false });
  },
}));
```

#### Chat Store
```tsx
// stores/chat-store.ts
import { create } from 'zustand';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatState {
  messages: Message[];
  isLoading: boolean;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  
  sendMessage: async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    
    set((state) => ({
      messages: [...state.messages, userMessage],
      isLoading: true,
    }));
    
    try {
      // API call to backend
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content }),
      });
      
      const data = await response.json();
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
      };
      
      set((state) => ({
        messages: [...state.messages, assistantMessage],
        isLoading: false,
      }));
    } catch (error) {
      set({ isLoading: false });
      console.error('Failed to send message:', error);
    }
  },
  
  clearMessages: () => set({ messages: [] }),
}));
```

## 🖥️ Desktop Application (Electron)

### Project Structure
```
charlie-desktop/
├── src/
│   ├── main/                # Main process
│   │   ├── index.ts         # Electron main process
│   │   ├── window.ts        # Window management
│   │   └── system.ts        # System integration
│   ├── renderer/            # Renderer process (React)
│   │   ├── components/      # Same as web components
│   │   ├── hooks/           # Desktop-specific hooks
│   │   └── utils/           # Desktop utilities
│   └── shared/              # Shared types and utilities
├── assets/                  # Application assets
├── build/                   # Build configuration
└── dist/                    # Distribution files
```

### Main Process Configuration
```typescript
// src/main/index.ts
import { app, BrowserWindow, ipcMain, Tray, Menu } from 'electron';
import path from 'path';

class CharlieApp {
  private mainWindow: BrowserWindow | null = null;
  private tray: Tray | null = null;

  constructor() {
    this.setupApp();
    this.setupIPC();
  }

  private setupApp() {
    app.whenReady().then(() => {
      this.createWindow();
      this.createTray();
    });

    app.on('window-all-closed', () => {
      if (process.platform !== 'darwin') {
        app.quit();
      }
    });
  }

  private createWindow() {
    this.mainWindow = new BrowserWindow({
      width: 1200,
      height: 800,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
        preload: path.join(__dirname, 'preload.js'),
      },
    });

    if (process.env.NODE_ENV === 'development') {
      this.mainWindow.loadURL('http://localhost:3000');
    } else {
      this.mainWindow.loadFile('dist/index.html');
    }
  }

  private setupIPC() {
    ipcMain.handle('get-system-info', () => {
      return {
        platform: process.platform,
        version: app.getVersion(),
      };
    });
  }
}

new CharlieApp();
```

## 💻 CLI Application (Python Rich)

### CLI Structure
```
charlie-cli/
├── charlie/
│   ├── __init__.py
│   ├── cli.py              # Main CLI entry point
│   ├── commands/
│   │   ├── chat.py         # Chat command
│   │   ├── voice.py        # Voice command
│   │   └── config.py       # Configuration command
│   ├── ui/
│   │   ├── components.py   # Rich UI components
│   │   └── layouts.py      # CLI layouts
│   └── utils/
│       ├── voice.py        # Voice utilities
│       └── config.py       # Configuration utilities
└── setup.py
```

### CLI Implementation
```python
# charlie/cli.py
import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from charlie.commands import chat, voice, config

console = Console()

@click.group()
@click.version_option()
def cli():
    """Charlie - Your AI Assistant in the terminal"""
    console.print(Panel(
        Text("Charlie AI Assistant", style="bold blue"),
        subtitle="Voice-controlled AI at your fingertips"
    ))

@cli.command()
def start():
    """Start interactive chat with Charlie"""
    chat.start_interactive_chat()

@cli.command()
@click.option('--listen', '-l', is_flag=True, help='Start voice interaction')
def voice(listen):
    """Voice interaction with Charlie"""
    if listen:
        voice.start_voice_session()
    else:
        console.print("Use --listen to start voice interaction")

if __name__ == '__main__':
    cli()
```

## 🎨 Design Principles

### 1. Consistency
- Use the same color palette across all platforms
- Maintain consistent typography and spacing
- Ensure uniform component behavior

### 2. Accessibility
- Follow WCAG 2.1 AA guidelines
- Provide keyboard navigation
- Include screen reader support
- Offer high contrast mode

### 3. Performance
- Lazy load components where possible
- Optimize bundle sizes
- Use efficient state management
- Implement proper caching strategies

### 4. Responsive Design
- Mobile-first approach
- Flexible grid systems
- Adaptive typography
- Touch-friendly interactions

## 🔧 Development Workflow

### 1. Setup Development Environment
```bash
# Web application
cd charlie-web
npm install
npm run dev

# Desktop application
cd charlie-desktop
npm install
npm run electron:dev

# CLI application
cd charlie-cli
pip install -e .
charlie --help
```

### 2. Code Quality Standards
```bash
# ESLint configuration
{
  "extends": [
    "next/core-web-vitals",
    "@typescript-eslint/recommended"
  ],
  "rules": {
    "prefer-const": "error",
    "no-unused-vars": "error"
  }
}

# Prettier configuration
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 80,
  "tabWidth": 2
}
```

### 3. Testing Strategy
```bash
# Unit tests
npm run test

# E2E tests
npm run test:e2e

# Visual regression tests
npm run test:visual
```

## 📱 Progressive Web App Features

### Service Worker
```typescript
// public/sw.js
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('charlie-v1').then((cache) => {
      return cache.addAll([
        '/',
        '/dashboard',
        '/static/js/bundle.js',
        '/static/css/main.css',
      ]);
    })
  );
});
```

### Manifest Configuration
```json
{
  "name": "Charlie AI Assistant",
  "short_name": "Charlie",
  "description": "Voice-controlled AI assistant",
  "start_url": "/",
  "display": "standalone",
  "theme_color": "#00b8d4",
  "background_color": "#0a0a0a",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    }
  ]
}
```

---

## 🚀 Deployment Guidelines

### Web Application
- Use Vercel for deployment
- Configure environment variables
- Set up domain and SSL
- Enable analytics and monitoring

### Desktop Application
- Build with electron-builder
- Configure auto-updater
- Set up code signing
- Create installer packages

### CLI Application
- Package with PyInstaller
- Distribute via pip/conda
- Create Windows installer
- Set up auto-completion

Follow [ROADMAP.md](./ROADMAP.md) for implementation timeline and [BACKEND_STRUCTURE.md](./BACKEND_STRUCTURE.md) for backend integration. 