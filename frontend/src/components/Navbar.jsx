import React, { useState } from 'react';

const Navbar = ({
  logo,
  logoText = 'Smart Scheduling',
  navigationLinks = [],
  profileMenu = null,
  brandLink = '/',
  className = '',
  variant = 'light',
  ...props
}) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const getVariantClass = () => {
    switch (variant) {
      case 'dark':
        return 'navbar-dark bg-dark';
      case 'primary':
        return 'navbar-dark bg-primary';
      case 'light':
      default:
        return 'navbar-light bg-light';
    }
  };

  return (
    <nav className={`navbar navbar-expand-lg ${getVariantClass()} ${className}`} {...props}>
      <div className="container-fluid">
        {/* Brand/Logo */}
        <a className="navbar-brand d-flex align-items-center" href={brandLink}>
          {logo && <img src={logo} alt="Logo" className="me-2" style={{ height: '32px' }} />}
          <span className="fw-bold">{logoText}</span>
        </a>

        {/* Mobile menu toggle */}
        <button
          className="navbar-toggler"
          type="button"
          onClick={toggleMenu}
          aria-controls="navbarNav"
          aria-expanded={isMenuOpen}
          aria-label="Toggle navigation"
        >
          <span className="navbar-toggler-icon"></span>
        </button>

        {/* Navigation menu */}
        <div className={`collapse navbar-collapse ${isMenuOpen ? 'show' : ''}`} id="navbarNav">
          <ul className="navbar-nav me-auto">
            {navigationLinks.map((link, index) => (
              <li key={index} className="nav-item">
                <a
                  className={`nav-link ${link.active ? 'active' : ''}`}
                  href={link.href}
                  aria-current={link.active ? 'page' : undefined}
                >
                  {link.icon && <i className={`${link.icon} me-1`}></i>}
                  {link.text}
                </a>
              </li>
            ))}
          </ul>

          {/* Profile menu */}
          {profileMenu && (
            <div className="navbar-nav">
              <div className="nav-item dropdown">
                <a
                  className="nav-link dropdown-toggle d-flex align-items-center"
                  href="#"
                  role="button"
                  data-bs-toggle="dropdown"
                  aria-expanded="false"
                >
                  {profileMenu.avatar && (
                    <img
                      src={profileMenu.avatar}
                      alt="Profile"
                      className="rounded-circle me-2"
                      style={{ width: '32px', height: '32px' }}
                    />
                  )}
                  {profileMenu.name}
                </a>
                <ul className="dropdown-menu dropdown-menu-end">
                  {profileMenu.items.map((item, index) => (
                    <li key={index}>
                      <a
                        className="dropdown-item"
                        href={item.href}
                        onClick={item.onClick}
                      >
                        {item.icon && <i className={`${item.icon} me-2`}></i>}
                        {item.text}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;