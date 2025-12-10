import React, { useState } from 'react';
import {
  Paper,
  TextField,
  Button,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Chip,
  IconButton,
  InputAdornment,
  CircularProgress
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import SearchIcon from '@mui/icons-material/Search';
import { motion } from 'framer-motion';

const exampleQueries = [
  "Compare Verstappen and Hamilton's performance in the 2024 Bahrain GP",
  "Analyze tire strategy for Mercedes in the 2024 Australian Grand Prix",
  "What was the fastest lap in the 2024 Saudi Arabian GP?",
  "Show me pit stop strategies for Red Bull vs Ferrari in 2024 Bahrain",
  "Compare sector times for top 3 drivers in 2024 Bahrain qualifying",
];

function QueryInput({ onSubmit, isAnalyzing }) {
  const [query, setQuery] = useState('');
  const [depth, setDepth] = useState('deep');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim() || isAnalyzing) return;
    await onSubmit(query, depth);
  };

  const handleExampleClick = (example) => {
    setQuery(example);
  };

  return (
    <Paper
      component={motion.div}
      whileHover={{ scale: 1.01 }}
      elevation={0}
      className="glass-panel"
      sx={{
        p: 4,
        borderRadius: 4,
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* Accent line */}
      <Box sx={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: '2px',
        background: 'linear-gradient(90deg, #e10600, #00d2be)'
      }} />

      <Typography variant="h5" gutterBottom sx={{ color: 'white', mb: 3, fontWeight: 700 }}>
        Analyze Race Data
      </Typography>

      <Box component="form" onSubmit={handleSubmit}>
        <TextField
          fullWidth
          multiline
          minRows={3}
          variant="outlined"
          placeholder="Ask about strategies, lap times, or driver comparisons..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={isAnalyzing}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start" sx={{ alignSelf: 'flex-start', mt: 1.5 }}>
                <SearchIcon sx={{ color: 'rgba(255,255,255,0.4)' }} />
              </InputAdornment>
            )
          }}
          sx={{
            mb: 3,
            '& .MuiOutlinedInput-root': {
              color: 'white',
              backgroundColor: 'rgba(0,0,0,0.2)',
              fontSize: '1.1rem',
              '& fieldset': {
                borderColor: 'rgba(255, 255, 255, 0.1)',
              },
              '&:hover fieldset': {
                borderColor: 'rgba(255, 255, 255, 0.2)',
              },
              '&.Mui-focused fieldset': {
                borderColor: '#e10600',
              },
            },
          }}
        />

        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mb: 3, flexWrap: 'wrap' }}>
          <FormControl sx={{ minWidth: 200, flexGrow: 1 }}>
            <InputLabel sx={{ color: 'rgba(255,255,255,0.7)' }}>Analysis Depth</InputLabel>
            <Select
              value={depth}
              label="Analysis Depth"
              onChange={(e) => setDepth(e.target.value)}
              disabled={isAnalyzing}
              sx={{
                color: 'white',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255, 255, 255, 0.1)',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255, 255, 255, 0.3)',
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderColor: '#e10600',
                },
                '& .MuiSvgIcon-root': {
                  color: 'white',
                },
              }}
            >
              <MenuItem value="basic">
                <Box>
                  <Typography variant="body1">Basic</Typography>
                  <Typography variant="caption" color="text.secondary">Dataset insights only</Typography>
                </Box>
              </MenuItem>
              <MenuItem value="deep">
                <Box>
                  <Typography variant="body1">Deep</Typography>
                  <Typography variant="caption" color="text.secondary">API + Telemetry Analysis</Typography>
                </Box>
              </MenuItem>
              <MenuItem value="story">
                <Box>
                  <Typography variant="body1">Story Mode</Typography>
                  <Typography variant="caption" color="text.secondary">Full narrative report</Typography>
                </Box>
              </MenuItem>
            </Select>
          </FormControl>

          <Button
            type="submit"
            variant="contained"
            size="large"
            endIcon={isAnalyzing ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
            disabled={!query.trim() || isAnalyzing}
            sx={{
              px: 5,
              py: 1.8,
              minWidth: 160,
              fontSize: '1rem',
            }}
          >
            {isAnalyzing ? 'Processing...' : 'Analyze'}
          </Button>
        </Box>

        <Box sx={{ mt: 3, pt: 3, borderTop: '1px solid rgba(255,255,255,0.05)' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <AutoAwesomeIcon sx={{ color: '#f1c40f', fontSize: 18 }} />
            <Typography variant="subtitle2" sx={{ color: 'rgba(255,255,255,0.6)', textTransform: 'uppercase', letterSpacing: 1 }}>
              Try these queries
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {exampleQueries.map((example, index) => (
              <Chip
                key={index}
                label={example}
                onClick={() => !isAnalyzing && handleExampleClick(example)}
                disabled={isAnalyzing}
                sx={{
                  background: 'rgba(255, 255, 255, 0.05)',
                  color: 'rgba(255,255,255,0.9)',
                  border: '1px solid transparent',
                  '&:hover': {
                    background: 'rgba(255, 255, 255, 0.1)',
                    borderColor: 'rgba(255,255,255,0.2)',
                    cursor: 'pointer'
                  },
                }}
              />
            ))}
          </Box>
        </Box>
      </Box>
    </Paper>
  );
}

// Helper to use CircularProgress inside button
export default QueryInput;
