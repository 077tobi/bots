// App.jsx
import React from 'react';
import './App.css';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './components/Home';

function App() {
  return (
    <Router>
      <div className="app">
        <Routes>
          <Route path="/" element={<Home />} />
        </Routes>
        <Navbar />
      </div>
    </Router>
  );
}

export default App;

// components/Home.jsx
import React from 'react';
import './Home.css';

function Home() {
  const featuredAnime = {
    title: "Fairy Tail: 100-nen Quest",
    duration: "24 min",
    genres: ["Fantasia", "Ação", "Aventura"],
    description: "Um ano depois que a guilda Fairy Tail superou as forças diabólicas de Acnologia e Zeref, Natsu e sua equipe viajam para o continente norte...",
  };

  const recentAnimes = [
    {
      id: 1,
      title: "Yuru Camp",
      image: "/images/yurucamp.jpg"
    },
    {
      id: 2,
      title: "Dragon Quest",
      image: "/images/dragonquest.jpg"
    },
    {
      id: 3,
      title: "One Piece",
      image: "/images/onepiece.jpg"
    }
  ];

  return (
    <div className="home">
      <div className="featured">
        <div className="featured__info">
          <h1>{featuredAnime.title}</h1>
          <div className="featured__metadata">
            <span>{featuredAnime.duration}</span>
            <span>{featuredAnime.genres.join(", ")}</span>
          </div>
          <p>{featuredAnime.description}</p>
          <div className="featured__buttons">
            <button className="btn-watch">Assistir</button>
            <button className="btn-list">+ Minha lista</button>
          </div>
        </div>
      </div>
      
      <div className="section">
        <h2>Últimos animes</h2>
        <div className="anime-row">
          {recentAnimes.map(anime => (
            <div key={anime.id} className="anime-card">
              <img src={anime.image} alt={anime.title} />
              <h3>{anime.title}</h3>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Home;

// components/Navbar.jsx
import React from 'react';
import { Link } from 'react-router-dom';
import './Navbar.css';

function Navbar() {
  return (
    <nav className="navbar">
      <Link to="/" className="nav-item">
        <i className="fas fa-home"></i>
        <span>Início</span>
      </Link>
      <Link to="/search" className="nav-item">
        <i className="fas fa-search"></i>
        <span>Buscar</span>
      </Link>
      <Link to="/bookmarks" className="nav-item">
        <i className="fas fa-bookmark"></i>
        <span>Salvos</span>
      </Link>
    </nav>
  );
}

export default Navbar;
