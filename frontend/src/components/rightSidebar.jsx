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
    <div className="w-64 bg-gray-800 text-white p-4 h-screen flex flex-col justify-between">
      {/* Progress Bar */}
      <div className="mb-6">
        <h4 className="text-sm text-center mb-2">Progress to Next Unlock</h4>
        <div className="w-full bg-gray-600 rounded-full h-2.5">
          <div
            className="bg-blue-500 h-2.5 rounded-full"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
        <div className="text-center text-sm mt-1">{progress}%</div>
      </div>

      <button className="mt-4 bg-blue-500 text-white p-2 rounded-md w-full flex justify-center items-center" onClick={updateProgress}>
        <FaShareAlt className="mr-2" />
        Share Conversation
      </button>
    </div>
  );
};

export default RightSidebar;

