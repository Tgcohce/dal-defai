import React from "react";
import Sidebar from "./components/leftSidebar";
import ChatWindow from "./components/chatWindow";
import RightSidebar from "./components/rightSidebar";

const App = () => {
  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar */}
      <Sidebar />

      {/* Main Chat Window */}
      <div className="flex-1 flex flex-col">
        <ChatWindow />
      </div>

      {/* Right Sidebar */}
      <RightSidebar />
    </div>
  );
};

export default App;
