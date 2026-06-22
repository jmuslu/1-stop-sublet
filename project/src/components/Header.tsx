export type View = 'home' | 'browse';

interface HeaderProps {
  view: View;
  onNavigate: (view: View) => void;
}

function Header({ view, onNavigate }: HeaderProps) {
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
      </nav>
    </header>
  );
}

export default Header;
