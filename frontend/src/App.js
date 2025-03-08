import React from "react";
import Sidebar from "./components/leftSidebar";
import ChatWindow from "./components/chatWindow";
import RightSidebar from "./components/rightSidebar";

const App = () => {
  return (
    <div className="flex h-screen">
      {/* Left Sidebar */}
      <Sidebar />

      {/* Main Chat Window */}
      <div className="flex-1 flex flex-col w-3/5">
        <ChatWindow />
      </div>

      {/* Right Sidebar */}
      <RightSidebar />
    </div>
  );
};

export default App;
