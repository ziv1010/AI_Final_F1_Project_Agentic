import React, { useRef } from 'react';
import {
  Container,
  AppBar,
  Toolbar,
  Typography,
  Box,
  ThemeProvider,
  CssBaseline,
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';

import QueryInput from './components/QueryInput';
import ProgressMonitor from './components/ProgressMonitor';
import ResultsViewer from './components/ResultsViewer';
import ConnectionStatus from './components/ConnectionStatus';
import { theme } from './theme/theme';
import { useAnalysis } from './hooks/useAnalysis';
import './App.css';

function App() {
  const {
    status,
    sessionStatus,
    progress,
    result,
    isAnalyzing,
    submitQuery
  } = useAnalysis();

  const resultsRef = useRef(null);

  const handleQuerySubmit = async (query, depth) => {
    await submitQuery(query, depth);
    // Scroll to progress/results
    setTimeout(() => {
      resultsRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box className="App app-bg">
        <div className="grid-overlay" />
        <div className="mesh-gradient" />

        <AppBar
          position="fixed"
          elevation={0}
          sx={{
            background: 'rgba(5, 7, 10, 0.85)',
            backdropFilter: 'blur(20px)',
            borderBottom: '1px solid rgba(255,255,255,0.05)',
            zIndex: 1200,
          }}
        >
          <Container maxWidth="xl">
            <Toolbar disableGutters sx={{ height: 80 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
                <Typography
                  variant="h4"
                  component="div"
                  sx={{
                    fontWeight: 900,
                    color: '#e10600',
                    letterSpacing: '-1px',
                    fontStyle: 'italic',
                    mr: 2,
                    display: 'flex',
                    alignItems: 'center',
                  }}
                >
                  F1<span style={{ color: 'white', fontStyle: 'normal', marginLeft: 4 }}>AGENTS</span>
                </Typography>
                <Box
                  sx={{
                    height: 24,
                    width: 2,
                    bgcolor: 'rgba(255,255,255,0.1)',
                    mx: 2,
                    display: { xs: 'none', sm: 'block' }
                  }}
                />
                <Typography variant="subtitle1" sx={{ color: 'rgba(255,255,255,0.6)', display: { xs: 'none', sm: 'block' } }}>
                  Advanced Telemetry & Strategy Analysis
                </Typography>
              </Box>
              <ConnectionStatus status={status} />
            </Toolbar>
          </Container>
        </AppBar>

        <Container maxWidth="xl" sx={{ pt: 16, pb: 8, position: 'relative', zIndex: 1 }}>
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            <Box
              className="hero-section glass-panel"
              sx={{
                p: { xs: 3, md: 5 },
                mb: 6,
                textAlign: 'left',
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', lg: '1.6fr 1fr' },
                gap: 6,
                alignItems: 'center',
                borderRadius: 4,
                position: 'relative',
                overflow: 'hidden',
              }}
            >
              {/* Decorative background element for the card */}
              <Box sx={{
                position: 'absolute',
                top: '-50%',
                right: '-10%',
                width: '600px',
                height: '600px',
                background: 'radial-gradient(circle, rgba(225,6,0,0.15) 0%, transparent 70%)',
                zIndex: 0
              }} />

              <Box sx={{ position: 'relative', zIndex: 1 }}>
                <Typography variant="overline" sx={{ color: '#00d2be', fontWeight: 700, letterSpacing: 2, mb: 1, display: 'block' }}>
                  AI-POWERED RACE ENGINEER
                </Typography>
                <Typography variant="h2" sx={{ color: 'white', mb: 2, lineHeight: 1.1, fontSize: { xs: '2.5rem', md: '3.5rem' } }}>
                  Precision Analytics.<br />
                  <span style={{ color: '#e10600' }}>Real-time Insights.</span>
                </Typography>
                <Typography variant="body1" sx={{ color: 'rgba(255,255,255,0.7)', lineHeight: 1.8, maxWidth: 600, fontSize: '1.1rem' }}>
                  Ask complex questions about strategy, tires, telemetry, and driver performance.
                  Our agentic pipeline analyzes millions of data points to deliver strat-room quality reports.
                </Typography>
              </Box>

              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', sm: 'repeat(3, 1fr)' },
                  gap: 2,
                  position: 'relative',
                  zIndex: 1,
                }}
              >
                <FeatureCard icon="🚀" title="Deep Telemetry" desc="Lap-by-lap comparison" />
                <FeatureCard icon="🌦️" title="Weather" desc="Track evolution impact" />
                <FeatureCard icon="🧠" title="Strategy" desc="Undercut & tire life" />
              </Box>
            </Box>
          </motion.div>

          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', lg: '1.4fr 1fr' },
              gap: 4,
              alignItems: 'start',
            }}
          >
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2, duration: 0.6 }}
            >
              <QueryInput onSubmit={handleQuerySubmit} isAnalyzing={isAnalyzing} />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3, duration: 0.6 }}
            >
              <Box className="glass-panel" sx={{ p: 4, borderRadius: 4 }}>
                <Typography variant="h6" sx={{ color: 'white', mb: 3, display: 'flex', alignItems: 'center' }}>
                  <span style={{ fontSize: '1.5em', marginRight: '10px' }}>💡</span> Pro Tips
                </Typography>
                <Box component="ul" sx={{
                  m: 0,
                  pl: 2,
                  color: 'rgba(255,255,255,0.7)',
                  '& li': { mb: 1.5, lineHeight: 1.6 }
                }}>
                  <li>Use <strong>"Story"</strong> depth for a comprehensive narrative report.</li>
                  <li>Compare drivers: <em>"Verstappen vs. Hamilton Bahrain 2024"</em>.</li>
                  <li>Analyze strategy: <em>"Ferrari pit stop strategy Saudi Arabia"</em>.</li>
                  <li>Telemetry takes time. Visuals appear automatically when ready.</li>
                </Box>
              </Box>
            </motion.div>
          </Box>

          <div ref={resultsRef} style={{ paddingTop: '20px' }}>
            <AnimatePresence mode='wait'>
              {(isAnalyzing || progress.length > 0) && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.5 }}
                >
                  <Box sx={{ mt: 6 }}>
                    <ProgressMonitor
                      progress={progress}
                      status={sessionStatus?.status}
                      sessionId={sessionStatus?.session_id} // sessionStatus might be null initially
                    />
                  </Box>
                </motion.div>
              )}

              {result && (
                <motion.div
                  initial={{ opacity: 0, y: 50 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6 }}
                >
                  <Box sx={{ mt: 6 }}>
                    <ResultsViewer result={result} />
                  </Box>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </Container>
      </Box>
    </ThemeProvider>
  );
}

function FeatureCard({ icon, title, desc }) {
  return (
    <Box
      className="glass-card"
      sx={{
        p: 2.5,
        borderRadius: 3,
        border: '1px solid rgba(255,255,255,0.05)',
        background: 'rgba(255, 255, 255, 0.03)',
        textAlign: 'left',
        transition: 'transform 0.2s',
        '&:hover': {
          transform: 'translateY(-5px)',
          background: 'rgba(255, 255, 255, 0.06)',
        }
      }}
    >
      <Typography variant="h3" sx={{ mb: 1, fontSize: '2rem' }}>{icon}</Typography>
      <Typography variant="subtitle1" sx={{ color: 'white', fontWeight: 600, mb: 0.5 }}>
        {title}
      </Typography>
      <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.5)' }}>
        {desc}
      </Typography>
    </Box>
  );
}

export default App;
