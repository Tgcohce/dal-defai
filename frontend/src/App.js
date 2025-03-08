import React from "react";
import Sidebar from "./components/sidebar";
import ChatWindow from "./components/chatWindow";

function App() {
  return (
    <div className="flex h-screen">
      <Sidebar/>
      <ChatWindow/>
    </div>
  );
}

export default App;
