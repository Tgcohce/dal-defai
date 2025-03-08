import React, { useState } from "react";
import { FaShareAlt } from "react-icons/fa"; // Import share icon

const RightSidebar = () => {
  const [progress, setProgress] = useState(50); // Set initial progress (50% as an example)

  // Function to update progress (could be based on an actual condition)
  const updateProgress = () => {
    if (progress < 100) {
      setProgress(progress + 10); // Increase progress by 10 (you can change this logic)
    }
  };

  return (
    <div className="w-64 bg-gray-900/95 backdrop-blur-sm text-white p-6 h-screen flex flex-col justify-between border-l border-gray-700/50">
      {/* Progress Bar */}
      <div className="mb-6">
        <h4 className="text-lg font-semibold text-center mb-4">Progress to Next Unlock</h4>
        <div className="w-full bg-gray-700 rounded-full h-3">
          <div
            className="bg-gradient-to-r from-blue-500 to-purple-500 h-3 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        <div className="text-center text-sm mt-2 text-gray-400">{progress}%</div>
      </div>

      <button 
        className="mt-4 bg-gradient-to-r from-blue-500 to-purple-500 text-white p-3 rounded-lg w-full flex justify-center items-center hover:opacity-90 transition-all duration-300 shadow-lg"
        onClick={updateProgress}
      >
        <FaShareAlt className="mr-2" />
        Share Conversation
      </button>
    </div>
  );
};

export default RightSidebar;

