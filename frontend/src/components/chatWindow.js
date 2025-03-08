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
    <div className="flex-1 flex flex-col w-full h-screen">
      <div className="flex-1 p-4 overflow-y-auto bg-gray-100">
        {messages.length === 0 ? (
          // Show welcome message when there are no messages
          <WelcomeMessage />
        ) : (
          messages.map((msg, index) => (
            <div
              key={index}
              className={`mb-2 p-3 rounded-lg max-w-3/4 ${
                msg.sender === "user" ? "bg-blue-500 text-white ml-auto" : "bg-gray-300 text-gray-900"
              }`}
            >
              <span className="font-bold">{msg.sender}:</span> {msg.text}
            </div>
          ))
        )}
      </div>
      <div className="p-4 bg-white border-t flex">
        <input
          type="text"
          className="flex-1 border p-2 rounded-md"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message..."
        />
        <button className="ml-2 bg-blue-500 text-white p-2 rounded-md" onClick={sendMessage}>
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;

