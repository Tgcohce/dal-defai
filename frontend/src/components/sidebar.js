import React from "react";

const Sidebar = () => {
  return (
    <div className="w-1/4 h-screen bg-gray-800 text-white p-4">
      <h2 className="text-lg font-bold">Chat Sessions</h2>
      <ul>
        <li className="p-2 cursor-pointer hover:bg-gray-700">New Chat</li>
      </ul>
    </div>
  );
};

export default Sidebar;
