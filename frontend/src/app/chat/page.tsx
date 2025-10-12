import { ChatBox } from '@/components/chat/ChatBox'

export default function ChatPage() {
  return (
    <div className="container mx-auto p-4 h-screen">
      <h1 className="text-2xl font-bold mb-4">Value Chat</h1>
      <div className="h-[calc(100vh-120px)]">
        <ChatBox />
      </div>
    </div>
  )
}
