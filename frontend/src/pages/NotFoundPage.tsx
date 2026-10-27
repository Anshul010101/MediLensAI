import React from 'react';
import { Link } from 'react-router-dom';
import { FileQuestion, ArrowLeft } from 'lucide-react';
import { Button } from '../components/common/Button';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="max-w-md mx-auto py-20 text-center space-y-4 animate-fade-in">
      <div className="w-16 h-16 mx-auto rounded-2xl bg-slate-100 text-slate-400 flex items-center justify-center">
        <FileQuestion className="w-8 h-8" />
      </div>
      <div className="space-y-1">
        <h1 className="text-xl font-bold text-slate-900">Page Not Found</h1>
        <p className="text-xs text-slate-500">
          The requested route does not exist or the report may have been deleted.
        </p>
      </div>
      <div className="pt-2">
        <Link to="/">
          <Button variant="primary" size="sm" icon={<ArrowLeft className="w-4 h-4" />}>
            Back to Dashboard
          </Button>
        </Link>
      </div>
    </div>
  );
};
