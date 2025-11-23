import { useEffect, useRef, useState } from 'react'
import { Hands, HAND_CONNECTIONS } from '@mediapipe/hands'
import { Camera } from '@mediapipe/camera_utils'
import { drawConnectors, drawLandmarks } from '@mediapipe/drawing_utils'

export default function HandStream({ onLandmarks }) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const cameraRef = useRef(null)
  const handsRef = useRef(null)
  const [running, setRunning] = useState(false)
  const lastSentRef = useRef(0)

  useEffect(() => {
    const hands = new Hands({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
    })
    hands.setOptions({
      maxNumHands: 2,
      modelComplexity: 1,
      minDetectionConfidence: 0.6,
      minTrackingConfidence: 0.6
    })
    hands.onResults(onResults)
    handsRef.current = hands

    return () => {
      try { handsRef.current?.close() } catch {}
      try { cameraRef.current?.stop() } catch {}
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const onResults = (results) => {
    const canvas = canvasRef.current
    const video = videoRef.current
    if (!canvas || !video) return
    // Resize canvas to video
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    ctx.save()
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.drawImage(results.image, 0, 0, canvas.width, canvas.height)

    // Draw and collect landmarks
    const all = results.multiHandLandmarks || []
    all.forEach(lm => {
      drawConnectors(ctx, lm, HAND_CONNECTIONS, { color: '#00FF00', lineWidth: 2 })
      drawLandmarks(ctx, lm, { color: '#FF0000', lineWidth: 1 })
    })
    ctx.restore()

    // If no hands, notify null to allow UI reset and model buffer reset
    if (!all.length) {
      if (onLandmarks) onLandmarks(null)
      return
    }

    // Flatten landmarks (two hands, 21 points each, x/y/z)
    const flat = []
    for (let h = 0; h < Math.min(2, all.length); h++) {
      const lm = all[h]
      for (let i = 0; i < lm.length; i++) {
        flat.push(lm[i].x, lm[i].y, lm[i].z ?? 0)
      }
    }
    while (flat.length < 126) flat.push(0)

    const now = performance.now()
    if (onLandmarks && now - lastSentRef.current > 50) { // ~20 FPS
      lastSentRef.current = now
      onLandmarks(flat.slice(0, 126))
    }
  }

  const start = async () => {
    if (running) return
    const video = videoRef.current
    const hands = handsRef.current
    if (!video || !hands) return

    // Set up camera
    const cam = new Camera(video, {
      onFrame: async () => {
        await hands.send({ image: video })
      },
      width: 640,
      height: 480
    })
    cameraRef.current = cam
    await cam.start()
    setRunning(true)
  }

  const stop = () => {
    cameraRef.current?.stop()
    setRunning(false)
  }

  return (
    <div className="handstream">
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 8 }}>
        {!running ? (
          <button onClick={start}>Start Camera</button>
        ) : (
          <button onClick={stop}>Stop Camera</button>
        )}
        <span>{running ? 'Camera running' : 'Camera stopped'}</span>
      </div>
      <div style={{ position: 'relative', width: 640, height: 480 }}>
        <video ref={videoRef} style={{ display: 'none' }} playsInline></video>
        <canvas ref={canvasRef} width={640} height={480} style={{ width: 640, height: 480, borderRadius: 8, border: '1px solid #ddd' }} />
      </div>
    </div>
  )
}
