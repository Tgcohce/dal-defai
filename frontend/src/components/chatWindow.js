import React, { useState } from "react";
import WelcomeMessage from './welcomeMessage'; // Import the new WelcomeMessage component

const ChatWindow = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const sendMessage = () => {
    if (input.trim()) {
      setMessages([...messages, { text: input, sender: "user" }]);
      setInput(""); // Clear input after sending
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
      <div className="flex-1 p-6 overflow-y-auto">
        {messages.length === 0 ? (
          <WelcomeMessage />
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`mb-4 p-4 rounded-xl max-w-2xl ${
                msg.sender === "user" 
                  ? "bg-gradient-to-r from-blue-500 to-purple-500 text-white ml-auto" 
                  : "bg-white text-gray-800 border border-gray-200 shadow-sm"
              }`}
            >
              <span className="font-medium">{msg.sender}:</span> {msg.text}
            </div>
          ))
        )}
      </div>
      <div className="p-6 bg-white border-t border-gray-200 shadow-lg">
        <div className="max-w-4xl mx-auto flex gap-3">
          <input
            type="text"
            className="flex-1 border border-gray-300 p-3 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
          />
          <button 
            className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-6 py-3 rounded-lg hover:opacity-90 transition-all duration-300 shadow-md"
            onClick={sendMessage}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatWindow;

