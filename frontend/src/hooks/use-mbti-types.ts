import { useState, useEffect } from 'react';
import { toast } from 'sonner';

interface RelationshipType {
  value: string;
  label: string;
}

interface MBTITypes {
  mbti_types: string[];
  relationship_types: RelationshipType[];
}

const CACHE_KEY = 'mbti_types_cache';
const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours in milliseconds

export function useMBTITypes() {
  const [mbtiTypes, setMBTITypes] = useState<string[]>([]);
  const [relationshipTypes, setRelationshipTypes] = useState<RelationshipType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMBTITypes = async () => {
      try {
        // Check cache first
        const cached = localStorage.getItem(CACHE_KEY);
        if (cached) {
          const { data, timestamp } = JSON.parse(cached);
          if (Date.now() - timestamp < CACHE_DURATION) {
            setMBTITypes(data.mbti_types);
            setRelationshipTypes(data.relationship_types);
            setIsLoading(false);
            return;
          }
        }

        // Fetch from API if cache is invalid or missing
        const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8181'}/api/mbti/types`);
        if (!response.ok) {
          throw new Error('Failed to fetch MBTI types');
        }

        const data: MBTITypes = await response.json();
        
        // Update state
        setMBTITypes(data.mbti_types);
        setRelationshipTypes(data.relationship_types);

        // Update cache
        localStorage.setItem(CACHE_KEY, JSON.stringify({
          data,
          timestamp: Date.now()
        }));

      } catch (err) {
        console.error('Error fetching MBTI types:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch MBTI types');
        toast.error('MBTI 유형을 불러오는데 실패했습니다.');
        
        // Fallback to default values if available in localStorage
        const cached = localStorage.getItem(CACHE_KEY);
        if (cached) {
          const { data } = JSON.parse(cached);
          setMBTITypes(data.mbti_types);
          setRelationshipTypes(data.relationship_types);
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchMBTITypes();
  }, []);

  return {
    mbtiTypes,
    relationshipTypes,
    isLoading,
    error
  };
} 