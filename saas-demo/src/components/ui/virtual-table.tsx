"use client";

import * as React from "react";
import { FixedSizeList as List } from "react-window";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

interface VirtualTableProps<T> {
  data: T[];
  columns: {
    header: string;
    accessor: keyof T | ((row: T) => React.ReactNode);
    className?: string;
    width?: number;
  }[];
  height?: number;
  rowHeight?: number;
  className?: string;
  onRowClick?: (row: T, index: number) => void;
  renderRow?: (row: T, index: number) => React.ReactNode;
}

export function VirtualTable<T extends { id?: string | number }>({
  data,
  columns,
  height = 400,
  rowHeight = 56,
  className,
  onRowClick,
  renderRow,
}: VirtualTableProps<T>) {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const row = data[index];
    
    if (!row) return null;

    if (renderRow) {
      return (
        <div style={style} onClick={() => onRowClick?.(row, index)}>
          {renderRow(row, index)}
        </div>
      );
    }

    return (
      <div
        style={style}
        onClick={() => onRowClick?.(row, index)}
        className={cn(
          "border-b hover:bg-muted/50 transition-colors",
          onRowClick && "cursor-pointer"
        )}
      >
        <div className="flex">
          {columns.map((column, colIndex) => {
            const value =
              typeof column.accessor === "function"
                ? column.accessor(row)
                : row[column.accessor];

            return (
              <div
                key={colIndex}
                className={cn(
                  "px-4 py-3 flex items-center",
                  column.className,
                  column.width && `w-[${column.width}px]`
                )}
                style={column.width ? { width: column.width } : { flex: 1 }}
              >
                {value as React.ReactNode}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  if (data.length === 0) {
    return (
      <div className={cn("flex items-center justify-center py-8 text-muted-foreground", className)}>
        暫無數據
      </div>
    );
  }

  return (
    <div className={cn("w-full", className)}>
      {/* 表頭 */}
      <div className="border-b bg-muted/50">
        <div className="flex">
          {columns.map((column, colIndex) => (
            <div
              key={colIndex}
              className={cn(
                "px-4 py-3 font-medium text-sm",
                column.className,
                column.width && `w-[${column.width}px]`
              )}
              style={column.width ? { width: column.width } : { flex: 1 }}
            >
              {column.header}
            </div>
          ))}
        </div>
      </div>

      {/* 虛擬滾動列表 */}
      <List
        height={height}
        itemCount={data.length}
        itemSize={rowHeight}
        width="100%"
        className="virtual-table-list"
      >
        {Row}
      </List>
    </div>
  );
}

// 傳統表格風格的虛擬滾動組件（使用 Table 組件）
interface VirtualTableListProps<T> {
  data: T[];
  columns: {
    header: string;
    accessor: keyof T | ((row: T) => React.ReactNode);
    className?: string;
  }[];
  height?: number;
  rowHeight?: number;
  className?: string;
  onRowClick?: (row: T, index: number) => void;
}

export function VirtualTableList<T extends { id?: string | number }>({
  data,
  columns,
  height = 400,
  rowHeight = 56,
  className,
  onRowClick,
}: VirtualTableListProps<T>) {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const row = data[index];
    
    if (!row) return null;

    return (
      <TableRow
        style={style}
        onClick={() => onRowClick?.(row, index)}
        className={cn(onRowClick && "cursor-pointer")}
      >
        {columns.map((column, colIndex) => {
          const value =
            typeof column.accessor === "function"
              ? column.accessor(row)
              : row[column.accessor];

          return (
            <TableCell key={colIndex} className={column.className}>
              {value as React.ReactNode}
            </TableCell>
          );
        })}
      </TableRow>
    );
  };

  if (data.length === 0) {
    return (
      <div className={cn("flex items-center justify-center py-8 text-muted-foreground", className)}>
        暫無數據
      </div>
    );
  }

  return (
    <div className={cn("w-full border rounded-md", className)}>
      <Table>
        <TableHeader>
          <TableRow>
            {columns.map((column, colIndex) => (
              <TableHead key={colIndex} className={column.className}>
                {column.header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
      </Table>

      {/* 虛擬滾動列表 */}
      <List
        height={height}
        itemCount={data.length}
        itemSize={rowHeight}
        width="100%"
        className="virtual-table-list"
      >
        {Row}
      </List>
    </div>
  );
}

