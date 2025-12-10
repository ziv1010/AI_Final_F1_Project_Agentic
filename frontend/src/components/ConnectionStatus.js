import React from 'react';
import { Box, Chip, CircularProgress, Typography } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WifiOffIcon from '@mui/icons-material/WifiOff';
import CloudQueueIcon from '@mui/icons-material/CloudQueue';

function ConnectionStatus({ status = 'disconnected' }) {
  const getStatusConfig = () => {
    switch (status) {
      case 'connected':
        return {
          label: 'SYSTEM ONLINE',
          color: '#00d2be', // Petronas Green
          icon: <CheckCircleIcon sx={{ fontSize: 16 }} />,
          bg: 'rgba(0, 210, 190, 0.1)',
          border: 'rgba(0, 210, 190, 0.3)'
        };
      case 'disconnected':
      case 'error':
        return {
          label: 'DISCONNECTED',
          color: '#e10600', // Ferrari Red
          icon: <WifiOffIcon sx={{ fontSize: 16 }} />,
          bg: 'rgba(225, 6, 0, 0.1)',
          border: 'rgba(225, 6, 0, 0.3)'
        };
      case 'connecting':
      default:
        return {
          label: 'CONNECTING...',
          color: '#f1c40f',
          icon: <CircularProgress size={12} thickness={5} sx={{ color: '#f1c40f' }} />,
          bg: 'rgba(241, 196, 15, 0.1)',
          border: 'rgba(241, 196, 15, 0.3)'
        };
    }
  };

  const config = getStatusConfig();

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          px: 1.5,
          py: 0.5,
          borderRadius: '50px',
          background: config.bg,
          border: `1px solid ${config.border}`,
          transition: 'all 0.3s ease'
        }}
      >
        <Box sx={{ color: config.color, display: 'flex' }}>
          {config.icon}
        </Box>
        <Typography
          variant="caption"
          sx={{
            color: config.color,
            fontWeight: 700,
            fontSize: '0.7rem',
            letterSpacing: '0.05em'
          }}
        >
          {config.label}
        </Typography>
      </Box>
    </Box>
  );
}

export default ConnectionStatus;
