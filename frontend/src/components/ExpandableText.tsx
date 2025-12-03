import React, { useState } from 'react';

interface ExpandableTextProps {
    text: string;
    maxLength?: number;
    className?: string;
}

export const ExpandableText: React.FC<ExpandableTextProps> = ({
    text,
    maxLength = 100,
    className = ""
}) => {
    const [isExpanded, setIsExpanded] = useState(false);

    if (!text) return null;

    if (text.length <= maxLength) {
        return <p className={className}>{text}</p>;
    }

    return (
        <div className={className}>
            <p className="whitespace-pre-wrap break-words">
                {isExpanded ? text : `${text.slice(0, maxLength)}...`}
            </p>
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    setIsExpanded(!isExpanded);
                }}
                className="text-purple-400 hover:text-purple-300 text-xs font-bold mt-1 hover:underline focus:outline-none"
            >
                {isExpanded ? 'Ver menos' : 'Ver mais'}
            </button>
        </div>
    );
};
