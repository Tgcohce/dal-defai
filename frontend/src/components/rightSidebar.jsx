import React from "react";
import { FaShareAlt } from "react-icons/fa"; // Import share icon

const RightSidebar = () => {
  return (
    <div className="w-64 bg-gray-800 text-white p-4 h-screen flex flex-col justify-between">
      <div className="flex flex-col items-center">
      </div>
      <button className="mt-4 bg-blue-500 text-white p-2 rounded-md w-full flex justify-center items-center">
        <FaShareAlt className="mr-2" />
        Share Conversation
      </button>
    </div>
  );
};

export default RightSidebar;
