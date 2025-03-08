import React, { useState } from "react";
import WelcomeMessage from './welcomeMessage';
import { FaPaperPlane } from 'react-icons/fa'; // Import paper plane icon

const ChatWindow = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const sendMessage = () => {
    if (input.trim()) {
      setMessages([...messages, { text: input, sender: "user" }]);
      setInput("");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex-1 flex flex-col w-full h-screen bg-gray-50">
      {/* Chat Header */}
      <div className="bg-white border-b border-gray-200 p-4 shadow-sm">
        <h2 className="text-xl font-semibold text-gray-800">Chat Session</h2>
      </div>

      {/* Messages Area */}
      <div className="flex-1 p-4 overflow-y-auto scroll-smooth">
        {messages.length === 0 ? (
          <WelcomeMessage />
        ) : (
          <div className="space-y-4">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`relative max-w-md px-4 py-2 rounded-xl ${
                    msg.sender === "user"
                      ? "bg-gradient-to-r from-blue-500 to-purple-500 text-white"
                      : "bg-white text-gray-800 border border-gray-200"
                  } shadow-md hover:shadow-lg transition-shadow duration-200`}
                >            
                  {/* Sender Badge */}
                  <div className={`text-xs mb-1 ${
                    msg.sender === "user" ? "text-blue-100" : "text-gray-500"
                  }`}>
                    {msg.sender === "user" ? "You" : "Assistant"}
                  </div>

                  {/* Message Text */}
                  <div className="relative z-10 text-sm whitespace-pre-wrap">
                    {msg.text}
                  </div>

                  {/* Timestamp */}
                  <div className={`mt-1 text-[10px] ${
                    msg.sender === "user" ? "text-blue-100" : "text-gray-400"
                  }`}>
                    {new Date().toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-6 bg-white border-t border-gray-200 shadow-lg">
        <div className="max-w-4xl mx-auto">
          <div className="relative flex items-center gap-4">
            <input
              type="text"
              className="flex-1 border-2 border-gray-300 p-4 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none bg-gray-50 transition-all duration-200"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message here..."
            />
            <button 
              className="bg-gradient-to-r from-blue-500 to-purple-500 text-white p-4 rounded-xl hover:opacity-90 transition-all duration-300 shadow-md flex items-center gap-2 min-w-[120px] justify-center"
              onClick={sendMessage}
            >
              <FaPaperPlane className="text-sm" />
              <span>Send</span>
            </button>
          </div>
          <div className="mt-2 text-xs text-gray-400 text-center">
            Press Enter to send, Shift + Enter for new line
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatWindow;

