import { Routes, Route } from 'react-router-dom'
import './App.css'
import Layout from './components/Layout'
import RepositoryList from './pages/RepositoryList'
import Dashboard from './pages/Dashboard'
import BugList from './pages/BugList'
import BugDetail from './pages/BugDetail'
import CommitList from './pages/CommitList'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<RepositoryList />} />
        <Route path="/repo/:id" element={<Dashboard />} />
        <Route path="/repo/:id/bugs" element={<BugList />} />
        <Route path="/repo/:id/bugs/:bugId" element={<BugDetail />} />
        <Route path="/repo/:id/commits" element={<CommitList />} />
      </Routes>
    </Layout>
  )
}
