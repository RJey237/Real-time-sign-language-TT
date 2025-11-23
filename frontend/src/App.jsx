import { useEffect, useRef, useState } from 'react'
import './App.css'
import UnifiedVideoChat from './UnifiedVideoChat'

// Determine protocol based on current location
const isHTTPS = window.location.protocol === 'https:'
const hostname = window.location.hostname
const API_BASE = `${isHTTPS ? 'https' : 'http'}://${hostname}:8000`
const WS_PROTOCOL = isHTTPS ? 'wss:' : 'ws:'
const WS_BASE = `${WS_PROTOCOL}//${hostname}:8000`
const WS_ASL = `${WS_BASE}/ws/asl/`

function App() {
  const [authUser, setAuthUser] = useState(null);

  return (
    <div className="container">
      <div className="header">
        <div className="title">ASL Translator + Video Chat</div>
      </div>

      <div className="grid">
        <div className="card">
          <h3 className="section-title">Authentication</h3>
          <AuthPanel onAuthSuccess={setAuthUser} />
        </div>

        {authUser && (
          <div className="card" style={{ gridColumn: '1 / -1' }}>
            <VideoAndChatPanel authUser={authUser} onLogout={() => setAuthUser(null)} />
          </div>
        )}
      </div>
    </div>
  )
}

export default App

function AuthPanel({ onAuthSuccess }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [me, setMe] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [errorMsg, setErrorMsg] = useState('')

  const api = async (path, body, method='POST') => {
    try {
      console.log(`[AUTH] Calling ${method} ${API_BASE}/api/${path}`, body)
      const res = await fetch(`${API_BASE}/api/${path}`, {
        method,
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: method==='GET' ? undefined : JSON.stringify(body||{})
      })
      
      console.log(`[AUTH] Response status: ${res.status}`)
      
      const responseText = await res.text()
      console.log(`[AUTH] Response text: ${responseText}`)
      
      if (!res.ok) {
        try {
          const data = JSON.parse(responseText)
          throw new Error(data.error || `HTTP ${res.status}`)
        } catch (e) {
          throw new Error(`HTTP ${res.status}: ${responseText.slice(0, 100)}`)
        }
      }
      
      const data = JSON.parse(responseText)
      console.log(`[AUTH] Success response:`, data)
      return data
    } catch (err) {
      console.error(`[AUTH] Error:`, err)
      throw err
    }
  }

  const register = async () => {
    if (!username || !password) {
      setErrorMsg('Please enter username and password')
      return
    }
    setErrorMsg('')
    setIsLoading(true)
    try {
      const data = await api('register/', { username, password })
      console.log('[AUTH] Register successful:', data)
      setMe(data)
      onAuthSuccess(data)
    } catch (e) {
      console.error('[AUTH] Register failed:', e.message)
      setErrorMsg('Register failed: ' + e.message)
    } finally {
      setIsLoading(false)
    }
  }
  
  const login = async () => {
    if (!username || !password) {
      setErrorMsg('Please enter username and password')
      return
    }
    setErrorMsg('')
    setIsLoading(true)
    try {
      const data = await api('login/', { username, password })
      console.log('[AUTH] Login successful:', data)
      setMe(data)
      onAuthSuccess(data)
    } catch (e) {
      console.error('[AUTH] Login failed:', e.message)
      setErrorMsg('Login failed: ' + e.message)
    } finally {
      setIsLoading(false)
    }
  }
  
  const logout = async () => {
    setErrorMsg('')
    setIsLoading(true)
    try {
      await api('logout/', {})
      setMe(null)
      onAuthSuccess(null)
      setUsername('')
      setPassword('')
    } catch (e) {
      console.error('[AUTH] Logout failed:', e.message)
      setErrorMsg('Logout failed: ' + e.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="auth">
      <div style={{ marginBottom: '1rem' }}>
        <input 
          placeholder="username" 
          value={username} 
          onChange={e=>setUsername(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && login()}
          disabled={isLoading || !!me}
        />
        <input 
          placeholder="password" 
          type="password" 
          value={password} 
          onChange={e=>setPassword(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && login()}
          disabled={isLoading || !!me}
        />
      </div>
      {errorMsg && (
        <div style={{ 
          backgroundColor: '#7f1d1d', 
          color: '#fca5a5',
          padding: '0.75rem',
          borderRadius: '6px',
          marginBottom: '1rem',
          fontSize: '0.9rem',
          border: '1px solid #ef4444'
        }}>
          {errorMsg}
        </div>
      )}
      {!me ? (
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button onClick={register} disabled={isLoading}>Register</button>
          <button onClick={login} disabled={isLoading}>Login</button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ 
            backgroundColor: '#0f3460', 
            padding: '0.75rem', 
            borderRadius: '6px',
            border: '1px solid #10b981'
          }}>
            <div><strong>✓ Logged in as:</strong> {me.username}</div>
            <div><strong>Your ID:</strong> {me.random_id}</div>
          </div>
          <button onClick={logout} style={{ backgroundColor: '#ef4444' }}>Logout</button>
        </div>
      )}
    </div>
  )
}

function ChatPanel() {
  const [targetId, setTargetId] = useState('')
  const [ws, setWs] = useState(null)
  const [chat, setChat] = useState([])
  const [text, setText] = useState('')
  const [myId, setMyId] = useState('')

  useEffect(()=>{
    // Try to fetch my random id from server; if not authenticated, leave blank
    fetch(`${API_BASE}/api/me/`, { credentials: 'include' })
      .then(r=>r.json())
      .then(d=>{ if (d.authenticated && d.random_id) setMyId(d.random_id) })
      .catch(()=>{})
    // Load any saved myId
    const saved = localStorage.getItem('myId')
    if (saved) setMyId(saved)
  }, [])

  const connectChat = () => {
    if (!targetId) return
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return
    // Ensure I have an id; generate ephemeral if missing
    let mine = myId?.trim()
    if (!mine) {
      mine = Math.random().toString(36).slice(2, 10).toUpperCase()
      setMyId(mine)
      localStorage.setItem('myId', mine)
    } else {
      localStorage.setItem('myId', mine)
    }
    const qs = `?self=${encodeURIComponent(mine)}`
    const sock = new WebSocket(`${WS_BASE}/ws/chat/${encodeURIComponent(targetId)}/${qs}`)
    sock.onopen = () => setChat(c=>[{sys:true, text:'Chat connected'},...c])
    sock.onclose = () => setChat(c=>[{sys:true, text:'Chat disconnected'},...c])
    sock.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data)
        if (data.type === 'message') {
          setChat(c=>[...c, { sender: data.sender, text: data.text }])
        } else if (data.type === 'prediction') {
          // forward to app for display
          window.dispatchEvent(new CustomEvent('remote-prediction', { detail: { label: data.label, confidence: data.confidence } }))
        }
      } catch {}
    }
    setWs(sock)
  }
  const send = () => {
    if (!ws || ws.readyState !== WebSocket.OPEN || !text) return
    ws.send(JSON.stringify({ type: 'message', text }))
    setText('')
  }
  const disconnect = () => ws && ws.close()

  return (
    <div className="chat">
      <h3>Chat</h3>
      <div>
        <input style={{width:180}} placeholder="My ID" value={myId} onChange={e=>setMyId(e.target.value)} />
        <input style={{width:220}} placeholder="Target Random ID" value={targetId} onChange={e=>setTargetId(e.target.value)} />
        <button className="btn-primary" onClick={connectChat}>Connect Chat</button>
        <button className="btn-danger" onClick={disconnect}>Disconnect</button>
      </div>
      <div className="chat-log">
        {chat.map((m,i)=>(
          <div key={i} className="chat-line">
            {m.sys ? <em>{m.text}</em> : <>
              <span className="sender">{m.sender}:</span>
              <span className="msg">{m.text}</span>
            </>}
          </div>
        ))}
      </div>
      <div>
        <input style={{width:360}} placeholder="message" value={text} onChange={e=>setText(e.target.value)} />
        <button className="btn-primary" onClick={send}>Send</button>
      </div>
    </div>
  )
}

function VideoAndChatPanel({ authUser, onLogout }) {
  const [targetId, setTargetId] = useState('')
  const [myId, setMyId] = useState(authUser?.random_id || '')
  const [ws, setWs] = useState(null)
  const [chat, setChat] = useState([])
  const [text, setText] = useState('')
  const [isConnected, setIsConnected] = useState(false)

  // Listen for ASL predictions from unified video
  useEffect(() => {
    const handler = (e) => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ 
          type: 'asl_prediction', 
          label: e.detail.label, 
          confidence: e.detail.confidence 
        }));
      }
    };
    window.addEventListener('asl-prediction-local', handler);
    return () => window.removeEventListener('asl-prediction-local', handler);
  }, [ws])

  const connectChat = () => {
    if (!targetId || !myId) {
      alert('Please enter peer ID')
      return
    }
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      return
    }
    
    const qs = `?self=${encodeURIComponent(myId)}`
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const BACKEND_HOST = window.location.hostname === 'localhost' ? '127.0.0.1' : window.location.hostname
    const wsUrl = `${protocol}//${BACKEND_HOST}:8000/ws/chat/${encodeURIComponent(targetId)}/${qs}`
    
    console.log('[Chat] Connecting to:', wsUrl)
    const sock = new WebSocket(wsUrl)
    
    sock.onopen = () => {
      console.log('[Chat] Connected')
      setIsConnected(true)
      setChat(c=>[{sys:true, text:'Chat connected'},...c])
    }
    
    sock.onclose = () => {
      console.log('[Chat] Disconnected')
      setIsConnected(false)
      setChat(c=>[{sys:true, text:'Chat disconnected'},...c])
    }
    
    sock.onerror = (err) => {
      console.error('[Chat] Error:', err)
      alert('Chat connection error')
    }
    
    sock.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data)
        console.log('[Chat] Message:', data)
        
        if (data.type === 'message') {
          setChat(c=>[...c, { sender: data.sender, text: data.text }])
        } else if (data.type === 'asl_prediction' || data.type === 'prediction') {
          // Relay remote ASL prediction to UnifiedVideoChat
          window.dispatchEvent(new CustomEvent('remote-asl-prediction', { 
            detail: { label: data.label, confidence: data.confidence } 
          }))
        }
      } catch (e) {
        console.error('[Chat] Parse error:', e)
      }
    }
    
    setWs(sock)
  }
  
  const send = () => {
    if (!ws || ws.readyState !== WebSocket.OPEN || !text) return
    ws.send(JSON.stringify({ type: 'message', text }))
    setText('')
  }
  
  const disconnect = () => {
    if (ws) {
      ws.close()
      setWs(null)
    }
    setIsConnected(false)
    setChat([])
    setTargetId('')
  }

  return (
    <div style={styles.videoChatContainer}>
      <div style={styles.videoSection}>
        <div style={styles.videoHeader}>
          <h3>📹 Video Chat with ASL Translation</h3>
          <button 
            onClick={onLogout}
            style={{ 
              padding: '0.5rem 1rem', 
              backgroundColor: '#ef4444', 
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            Logout
          </button>
        </div>
        <UnifiedVideoChat 
          targetId={targetId} 
          myId={myId}
          isConnected={isConnected}
        />
      </div>

      <div style={styles.chatSection}>
        <h3 style={{ margin: '0 0 1rem 0' }}>💬 Text Chat</h3>
        
        <div style={styles.chatInputs}>
          <div style={styles.idBox}>
            <span style={{ fontSize: '0.85rem', color: '#888' }}>Your ID:</span>
            <input 
              style={{...styles.input, backgroundColor: '#0f3460'}} 
              value={myId} 
              disabled 
            />
          </div>
          <div style={styles.idBox}>
            <span style={{ fontSize: '0.85rem', color: '#888' }}>Peer ID:</span>
            <input 
              style={styles.input}
              placeholder="Enter peer's random ID..." 
              value={targetId} 
              onChange={e=>setTargetId(e.target.value)}
              onKeyPress={e => e.key === 'Enter' && connectChat()}
            />
          </div>
          <button 
            onClick={connectChat} 
            disabled={isConnected}
            style={styles.connectBtn}
          >
            {isConnected ? '✓ Connected' : 'Connect'}
          </button>
          {isConnected && (
            <button 
              onClick={disconnect}
              style={styles.disconnectBtn}
            >
              Disconnect
            </button>
          )}
        </div>

        <div style={styles.chatLog}>
          {chat.length === 0 ? (
            <div style={{ color: '#666', textAlign: 'center', padding: '1rem' }}>
              No messages yet
            </div>
          ) : (
            chat.map((m,i)=>(
              <div key={i} style={styles.chatLine}>
                {m.sys ? (
                  <em style={{ color: '#888', fontSize: '0.8rem' }}>{m.text}</em>
                ) : (
                  <>
                    <span style={styles.sender}>{m.sender}:</span>
                    <span style={styles.msg}>{m.text}</span>
                  </>
                )}
              </div>
            ))
          )}
        </div>

        {isConnected && (
          <div style={styles.chatInput}>
            <input 
              style={styles.messageInput}
              placeholder="Type message..." 
              value={text} 
              onChange={e=>setText(e.target.value)}
              onKeyPress={e => e.key === 'Enter' && send()}
            />
            <button 
              onClick={send}
              style={styles.sendBtn}
            >
              Send
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

const styles = {
  videoChatContainer: {
    display: 'grid',
    gridTemplateColumns: '2fr 1fr',
    gap: '1.5rem',
    alignItems: 'start',
  },
  videoSection: {
    minWidth: 0,
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem'
  },
  videoHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    margin: '0 0 0.5rem 0'
  },
  chatSection: {
    backgroundColor: '#0f3460',
    borderRadius: '12px',
    padding: '1.5rem',
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
    maxHeight: '700px',
    border: '1px solid rgba(16,185,129,0.2)'
  },
  chatInputs: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
  },
  idBox: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.35rem'
  },
  input: {
    padding: '0.75rem',
    backgroundColor: '#1a1a2e',
    border: '1px solid rgba(16,185,129,0.3)',
    color: '#e0e0e0',
    borderRadius: '8px',
    fontSize: '0.9rem',
  },
  connectBtn: {
    padding: '0.75rem',
    backgroundColor: '#10b981',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: '600',
    fontSize: '0.95rem',
  },
  disconnectBtn: {
    padding: '0.75rem',
    backgroundColor: '#ef4444',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: '600',
    fontSize: '0.95rem',
  },
  chatLog: {
    flex: 1,
    overflow: 'auto',
    backgroundColor: '#1a1a2e',
    borderRadius: '8px',
    padding: '1rem',
    minHeight: '250px',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.75rem',
  },
  chatLine: {
    padding: '0.5rem',
    fontSize: '0.9rem',
    color: '#e5e7eb',
    wordWrap: 'break-word',
    lineHeight: '1.4'
  },
  sender: {
    color: '#10b981',
    fontWeight: '700',
    marginRight: '0.5rem',
  },
  msg: {
    color: '#e5e7eb',
  },
  chatInput: {
    display: 'flex',
    gap: '0.75rem',
  },
  messageInput: {
    flex: 1,
    padding: '0.75rem',
    backgroundColor: '#1a1a2e',
    border: '1px solid rgba(16,185,129,0.3)',
    color: '#e0e0e0',
    borderRadius: '8px',
    fontSize: '0.9rem',
  },
  sendBtn: {
    padding: '0.75rem 1.5rem',
    backgroundColor: '#10b981',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: '600',
    fontSize: '0.95rem',
  }
}
