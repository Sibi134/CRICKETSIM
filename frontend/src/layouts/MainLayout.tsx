import { Link, Outlet, useLocation } from 'react-router-dom';
import { Home, Users, Calendar, Activity, Trophy, History, Settings } from 'lucide-react';
import clsx from 'clsx';

const navItems = [
  { name: 'Dashboard', path: '/', icon: Home },
  { name: 'Teams', path: '/teams', icon: Users },
  { name: 'Schedule', path: '/schedule', icon: Calendar },
  { name: 'Live Matches', path: '/live', icon: Activity },
  { name: 'Points Table', path: '/standings', icon: Trophy },
  { name: 'Playoffs', path: '/playoffs', icon: Trophy },
  { name: 'History', path: '/history', icon: History },
  { name: 'Settings', path: '/settings', icon: Settings },
];

export const MainLayout = () => {
  const location = useLocation();

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 bg-surface border-r border-slate-700 hidden md:flex md:flex-col">
        <div className="h-16 flex items-center px-6 border-b border-slate-700">
          <h1 className="text-xl font-bold text-white tracking-wider">CRICKET<span className="text-primary">SIM</span></h1>
        </div>
        
        <nav className="flex-1 overflow-y-auto py-4">
          <ul className="space-y-1 px-3">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    className={clsx(
                      'flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors',
                      isActive 
                        ? 'bg-primary/10 text-primary' 
                        : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                    )}
                  >
                    <Icon className={clsx('mr-3 h-5 w-5 flex-shrink-0', isActive ? 'text-primary' : 'text-slate-400')} />
                    {item.name}
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Top Header Mobile (simplistic for now) */}
        <header className="h-16 flex items-center justify-between px-4 bg-surface border-b border-slate-700 md:hidden">
          <h1 className="text-xl font-bold text-white tracking-wider">CRICKET<span className="text-primary">SIM</span></h1>
        </header>

        <main className="flex-1 overflow-y-auto bg-background p-6">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};
