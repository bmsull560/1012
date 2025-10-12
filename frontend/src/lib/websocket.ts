export class WebSocketManager {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  
  connect(workspaceId: string) {
    const url = `ws://localhost:8000/api/v1/ws/${workspaceId}`
    this.ws = new WebSocket(url)
    
    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
    }
    
    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data)
      this.handleMessage(message)
    }
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }
    
    this.ws.onclose = () => {
      this.reconnect(workspaceId)
    }
  }
  
  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
  
  private handleMessage(message: any) {
    // Emit to subscribers
    console.log('Received:', message)
  }
  
  private reconnect(workspaceId: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        this.reconnectAttempts++
        this.connect(workspaceId)
      }, 1000 * this.reconnectAttempts)
    }
  }
  
  disconnect() {
    this.ws?.close()
  }
}
