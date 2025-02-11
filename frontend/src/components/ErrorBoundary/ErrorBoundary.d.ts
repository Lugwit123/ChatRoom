import React from 'react';

export interface ErrorBoundaryProps {
    children: React.ReactNode;
    fallback?: React.ReactNode;
}

export default class ErrorBoundary extends React.Component<ErrorBoundaryProps> {} 