import { useState, useRef, useEffect } from "react";
import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Link } from "react-router-dom";
import { MessageCircle, Image as ImageIcon, Heart, User, Send, Phone, Settings, Mic, Camera } from "lucide-react";

interface Message {
  id: string;
  sender: "user" | "ai";
  text: string;
  time: string;
  image?: string;
  voice?: string;
}

const ChatPage = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      sender: "ai",
      text: "안녕, 오늘 만나서 반가워! 나는 너의 AI 친구미나야, 어떻게지내고있어?",
      time: "오전 10:23",
    },
  ]);
  
  const [inputMessage, setInputMessage] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  const handleSendMessage = () => {
    if (inputMessage.trim() === "") return;
    
    const newMessage: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: inputMessage,
      time: new Date().toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit', hour12: true }),
    };
    
    setMessages([...messages, newMessage]);
    setInputMessage("");
    
    // Simulate AI response after a short delay
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        sender: "ai",
        text: "네 메시지 잘 받았어! 더 이야기해줘.",
        time: new Date().toLocaleTimeString('ko-KR', { hour: 'numeric', minute: '2-digit', hour12: true }),
      };
      setMessages(prev => [...prev, aiResponse]);
    }, 1000);
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar */}
      <div className="w-72 border-r bg-white hidden lg:block">
        {/* Add left sidebar content here */}
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col max-w-3xl mx-auto w-full border-x">
      {/* Header */}
      <header className="py-3 px-4 bg-white border-b flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Avatar className="h-8 w-8">
            <img src="/example_avatar_profile.png" alt="AI Friend" className="w-full h-full object-cover" />
          </Avatar>
          <div>
            <h1 className="text-sm">미나</h1>
            <p className="text-[11px] text-green-600">활동중 상태</p>
          </div>
        </div>
        <div className="flex gap-3">
          <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-gray-100">
            <Phone className="h-5 w-5" />
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-gray-100">
            <Settings className="h-5 w-5" />
          </Button>
        </div>
      </header>

      {/* Messages Container */}
      <div className="flex-grow overflow-auto px-4 py-2 bg-gray-50">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`mb-4 flex ${message.sender === "user" ? "justify-end" : "justify-start"}`}
          >
            {message.sender === "ai" && (
              <Avatar className="h-8 w-8 shrink-0">
                <img src="/example_avatar_profile.png" alt="AI Friend" className="w-full h-full object-cover" />
              </Avatar>
            )}
            <div className="flex flex-col max-w-[70%] mx-2">
              <div 
                className={`rounded-2xl p-3 ${message.sender === "user" 
                  ? "bg-blue-100 rounded-tr-none" 
                  : "bg-gray-100 rounded-tl-none"}`}
              >
                <p className="text-sm text-gray-800">{message.text}</p>
                {message.image && (
                  <div className="mt-2 rounded-lg overflow-hidden">
                    <img src={message.image} alt="Shared image" className="w-full h-auto" />
                  </div>
                )}
              </div>
              <span className="text-[11px] text-gray-500 mt-1 mx-1">{message.time}</span>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>



      {/* Input Section */}
      <div className="p-4 bg-white border-t">
        <div className="flex items-center gap-2 relative">
          <div className="flex-1 flex items-center bg-gray-100 rounded-full pr-2">
            <Textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="메시지를 입력하세요..."
              className="resize-none min-h-[40px] max-h-24 bg-transparent flex-1 py-2 pl-4 pr-20 focus:outline-none"
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
            />
            <div className="flex items-center gap-1">
              <button className="p-1 hover:bg-gray-200 rounded-full">
                <Mic className="h-5 w-5 text-gray-500" />
              </button>
              <button className="p-1 hover:bg-gray-200 rounded-full">
                <Camera className="h-5 w-5 text-gray-500" />
              </button>
            </div>
          </div>
          <Button 
            onClick={handleSendMessage} 
            className="shrink-0 h-10 w-10 rounded-full bg-blue-500 hover:bg-blue-600"
            disabled={!inputMessage.trim()}
          >
            <Send className="h-5 w-5 text-white" />
          </Button>
        </div>
      </div>

      {/* Bottom Navigation */}
      <nav className="py-2 grid grid-cols-4 border-t bg-white">
        <Link to="/" className="flex flex-col items-center justify-center">
          <MessageCircle className="h-6 w-6 text-blue-500" />
          <span className="text-[11px] text-blue-500 mt-1">채팅</span>
        </Link>
        <button className="flex flex-col items-center justify-center">
          <ImageIcon className="h-6 w-6 text-gray-400" />
          <span className="text-[11px] text-gray-400 mt-1">앨범</span>
        </button>
        <button className="flex flex-col items-center justify-center">
          <Heart className="h-6 w-6 text-gray-400" />
          <span className="text-[11px] text-gray-400 mt-1">추억</span>
        </button>
        <Link to="/profile" className="flex flex-col items-center justify-center">
          <User className="h-6 w-6 text-gray-400" />
          <span className="text-[11px] text-gray-400 mt-1">프로필</span>
        </Link>
      </nav>
      </div>

      {/* Right Sidebar */}
      <div className="w-72 border-l bg-white hidden lg:block">
        {/* Add right sidebar content here */}
      </div>
    </div>
  );
};

export default ChatPage;
