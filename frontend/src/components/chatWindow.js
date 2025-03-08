import React, { useState } from "react";

const ChatWindow = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");

  const sendMessage = () => {
    if (input.trim()) {
      setMessages([...messages, { text: input, sender: "user" }]);
      setInput(""); // Clear input after sending
    }
  };

  return (
    <div className="w-3/4 h-screen flex flex-col">
      <div className="flex-1 p-4 overflow-y-auto bg-gray-100">
        {messages.map((msg, index) => (
          <div key={index} className="mb-2">
            <span className="font-bold">{msg.sender}:</span> {msg.text}
          </div>
        ))}
      </div>
      <div className="p-4 bg-white border-t flex">
        <input
          type="text"
          className="flex-1 border p-2"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message..."
        />
        <button className="ml-2 bg-blue-500 text-white p-2" onClick={sendMessage}>
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;
