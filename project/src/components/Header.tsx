import type { Theme } from '../hooks/useTheme';

export type View = 'home' | 'browse';

interface HeaderProps {
  view: View;
  onNavigate: (view: View) => void;
  theme: Theme;
  onToggleTheme: () => void;
}

function Header({ view, onNavigate, theme, onToggleTheme }: HeaderProps) {
  return (
    <header className="navbar">
      <button className="brand" onClick={() => onNavigate('home')}>
        1StopSublet
      </button>
      <nav className="nav-links">
        <button
          className={`nav-link ${view === 'home' ? 'active' : ''}`}
          onClick={() => onNavigate('home')}
        >
          Home
        </button>
        <button
          className={`nav-link ${view === 'browse' ? 'active' : ''}`}
          onClick={() => onNavigate('browse')}
        >
          Browse
        </button>
        <button
          className="theme-toggle"
          onClick={onToggleTheme}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {theme === 'dark' ? (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          )}
          <span>{theme === 'dark' ? 'Light' : 'Dark'}</span>
        </button>
      </nav>
    </header>
  );
}

export default Header;
