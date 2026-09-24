import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';

interface SSEMessage {
  type: string;
  data: any;
}

export function useEvents(onEvent?: (event: SSEMessage) => void) {
  const queryClient = useQueryClient();

  useEffect(() => {
    const es = new EventSource('/api/v1/events');

    es.onopen = () => {
      // connected
    };

    es.onerror = () => {
      // EventSource auto-retries connection
    };

    const handleMessage = (type: string, ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data);
        const sseMsg: SSEMessage = { type, data };

        // Automatically invalidate related queries for instant reactivity
        if (type.startsWith('job.')) {
          queryClient.invalidateQueries({ queryKey: ['jobs'] });
          queryClient.invalidateQueries({ queryKey: ['status'] });
          queryClient.invalidateQueries({ queryKey: ['assets'] });
        } else if (type.startsWith('generation.')) {
          queryClient.invalidateQueries({ queryKey: ['jobs'] });
        } else if (type.startsWith('asset.')) {
          queryClient.invalidateQueries({ queryKey: ['assets'] });
        }

        if (onEvent) {
          onEvent(sseMsg);
        }
      } catch (err) {
        // ignore parse error
      }
    };

    const eventTypes = [
      'connected',
      'job.created',
      'job.started',
      'job.completed',
      'job.failed',
      'job.cancelled',
      'job.retried',
      'generation.created',
      'generation.state_changed',
      'generation.progress',
      'asset.created',
      'auth.required',
    ];

    eventTypes.forEach((t) => {
      es.addEventListener(t, (ev) => handleMessage(t, ev as MessageEvent));
    });

    return () => {
      es.close();
    };
  }, [queryClient, onEvent]);
}
