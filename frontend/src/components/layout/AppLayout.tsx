import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import BottomPanel from "./BottomPanel";

export default function AppLayout() {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
        <BottomPanel />
      </div>
    </div>
  );
}
