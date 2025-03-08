import React from 'react';

const WelcomeMessage = () => {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="max-w-2xl w-full bg-white p-8 rounded-2xl shadow-xl border border-gray-100">
          <h1 className="text-3xl font-bold mb-6 bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent text-center">
            Welcome to Curtis Portal
          </h1>
          
          <div className="space-y-6">
            <div className="p-4 bg-gray-50 rounded-xl">
              <p className="text-gray-700 text-lg mb-2">
                👋 Start a conversation to explore the possibilities!
              </p>
              <p className="text-gray-500">
                Type your message in the chat box below to begin.
              </p>
            </div>

            <div className="border-t border-gray-100 pt-6">
              <p className="text-sm text-center text-gray-500">
                Crafted with ❤️ by{" "}
                <span className="font-medium bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
                  Dalhousie Blockchain Society Dev Team
                </span>
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  };

export default WelcomeMessage;
