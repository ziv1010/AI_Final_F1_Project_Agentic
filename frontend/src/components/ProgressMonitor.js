import React, { useEffect, useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Chip,
  LinearProgress,
  CircularProgress
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import RadarIcon from '@mui/icons-material/Radar';
import DataUsageIcon from '@mui/icons-material/DataUsage';
import { motion, AnimatePresence } from 'framer-motion';
import moment from 'moment';

const nodeLabels = {
  'query_interpreter': 'Interpreting Query',
  'query_validator': 'Validating Query',
  'factor_analyzer': 'Analyzing Key Factors',
  'data_loader': 'Loading Race Data',
  'analysis_planner': 'Planning Analysis',
  'plan_reviewer': 'Reviewing Plan',
  'code_writer': 'Generating Analysis Code',
  'code_debugger': 'Debugging Code',
  'report_generator': 'Generating Report',
  'deep_analysis_fetcher': 'Fetching Telemetry Data',
  'deep_visualizer': 'Creating Visualizations',
  'deep_report_generator': 'Generating Deep Analysis',
  'storyteller': 'Creating Narrative',
};

function ProgressMonitor({ progress, status, sessionId }) {
  // Keep track of the active step based on progress
  const [activeStep, setActiveStep] = useState(0);

  // Group progress by node to determine steps
  const nodeProgress = progress.reduce((acc, item) => {
    if (item.node) {
      if (!acc[item.node]) {
        acc[item.node] = [];
      }
      acc[item.node].push(item);
    }
    return acc;
  }, {});

  const nodes = Object.keys(nodeProgress);

  useEffect(() => {
    setActiveStep(Math.max(0, nodes.length - 1));
  }, [nodes.length]);

  return (
    <Paper
      className="glass-panel"
      elevation={0}
      sx={{
        p: 4,
        borderRadius: 4,
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <RadarIcon sx={{ color: '#00d2be', fontSize: 28 }} className={status !== 'completed' ? "spin-slow" : ""} />
          <Box>
            <Typography variant="h6" sx={{ color: 'white', lineHeight: 1 }}>
              System Status
            </Typography>
            <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.5)', fontFamily: 'monospace' }}>
              SESSION ID: {sessionId || '---'}
            </Typography>
          </Box>
        </Box>

        <Chip
          label={status?.toUpperCase() || 'INITIALIZING'}
          color={status === 'completed' ? 'success' : status === 'error' ? 'error' : 'primary'}
          icon={status === 'completed' ? <CheckCircleIcon /> : <DataUsageIcon className="spin" />}
          sx={{ fontWeight: 700 }}
        />
      </Box>

      {/* Progress Bar Visual */}
      <Box sx={{ mb: 4 }}>
        <LinearProgress
          variant={status === 'completed' ? "determinate" : "indeterminate"}
          value={status === 'completed' ? 100 : 0}
          sx={{
            height: 6,
            borderRadius: 3,
            bgcolor: 'rgba(255,255,255,0.1)',
            '& .MuiLinearProgress-bar': {
              background: 'linear-gradient(90deg, #e10600, #ff4500)',
            }
          }}
        />
      </Box>

      <Stepper activeStep={activeStep} orientation="vertical">
        {nodes.map((node, index) => {
          const nodeItems = nodeProgress[node];
          const lastItem = nodeItems[nodeItems.length - 1];
          const nodeStatus = lastItem.status;
          const isError = nodeStatus === 'error' || nodeStatus === 'failed';
          const isCompleted = nodeStatus === 'completed';

          return (
            <Step key={node} completed={isCompleted} expanded={true}>
              <StepLabel
                error={isError}
                StepIconComponent={(props) => (
                  <StepIcon {...props} isError={isError} isCompleted={isCompleted} />
                )}
                sx={{
                  '& .MuiStepLabel-label': {
                    color: isError ? '#e10600' : 'white',
                    fontWeight: props => props.active ? 700 : 400
                  },
                }}
              >
                {nodeLabels[node] || node}
              </StepLabel>
              <StepContent>
                <Box sx={{
                  pl: 2,
                  borderLeft: '1px dashed rgba(255,255,255,0.2)',
                  ml: '12px'
                }}>
                  <AnimatePresence>
                    {nodeItems.map((item, idx) => (
                      <motion.div
                        key={idx}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.3, delay: idx * 0.1 }}
                      >
                        <Typography
                          variant="body2"
                          sx={{
                            color: 'rgba(255,255,255,0.6)',
                            fontFamily: 'monospace',
                            fontSize: '0.85rem',
                            mb: 0.5,
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1
                          }}
                        >
                          <span style={{ color: 'rgba(255,255,255,0.3)' }}>
                            {moment(item.timestamp).format('HH:mm:ss')}
                          </span>
                          {item.message}
                        </Typography>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </Box>
              </StepContent>
            </Step>
          );
        })}
      </Stepper>
    </Paper>
  );
}

function StepIcon({ active, completed, error, isError, isCompleted }) {
  let color = 'rgba(255,255,255,0.2)';
  let icon = null;

  if (isError || error) {
    color = '#e10600';
    icon = <ErrorIcon fontSize="small" sx={{ color: 'white' }} />;
  } else if (isCompleted || completed) {
    color = '#00d2be';
    icon = <CheckCircleIcon fontSize="small" sx={{ color: 'white' }} />;
  } else if (active) {
    color = '#e10600';
    icon = <CircularProgress size={14} thickness={6} sx={{ color: 'white' }} />;
  }

  return (
    <Box
      sx={{
        width: 24,
        height: 24,
        borderRadius: '50%',
        background: color,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1
      }}
    >
      {icon ? icon : <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'white' }} />}
    </Box>
  );
}

export default ProgressMonitor;
