import React, { useState } from "react";
import { FaCog, FaArrowLeft, FaArrowRight } from "react-icons/fa"; // Importing arrow icons

const Sidebar = () => {
  const [isOpen, setIsOpen] = useState(true);

  const toggleSidebar = () => {
    setIsOpen(!isOpen);
  };

  return (
    <div
      className={`h-screen bg-gray-800 text-white p-4 transition-all duration-300 ${
        isOpen ? "w-64" : "w-16"
      }`} // Conditional class for dynamic width
    >
      {/* Header with Settings, Sign In Button, and Collapsible Arrow */}
      <div className="flex justify-between items-center">
        <button
          onClick={toggleSidebar}
          className="text-white text-2xl p-2 cursor-pointer hover:text-gray-400"
        >
          {isOpen ? (
            <FaArrowLeft />
          ) : (
            <FaArrowRight />
          )}
        </button>
        <button
          onClick={() => alert("Sign In Clicked")}
          className="bg-blue-500 text-white p-2 rounded-md cursor-pointer hover:bg-blue-600"
        >
          Sign In
        </button>
        <button onClick={() => alert("Settings Clicked")}>
          <FaCog className="text-white text-2xl cursor-pointer hover:text-gray-400" />
        </button>
      </div>
      <div className="flex justify-center items-center mt-4">
        <h2 className="text-lg font-bold">Curtis Portal</h2>
      </div>
    </div>
  );
};

export default Sidebar;
