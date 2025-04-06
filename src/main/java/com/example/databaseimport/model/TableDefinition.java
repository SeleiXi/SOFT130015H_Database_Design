package com.example.databaseimport.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TableDefinition {
    private String tableName;
    private List<ColumnDefinition> columns = new ArrayList<>();
    private List<String> primaryKeys = new ArrayList<>();
    private List<ForeignKeyDefinition> foreignKeys = new ArrayList<>();
    
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ColumnDefinition {
        private String name;
        private String type;
        private boolean nullable;
        private String defaultValue;
        private int position;
        
        public String toSqlDefinition() {
            StringBuilder sb = new StringBuilder();
            sb.append(name).append(" ").append(type);
            
            if (!nullable) {
                sb.append(" NOT NULL");
            }
            
            if (defaultValue != null) {
                sb.append(" DEFAULT ").append(defaultValue);
            }
            
            return sb.toString();
        }
    }
    
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ForeignKeyDefinition {
        private List<String> columns = new ArrayList<>();
        private String referenceTable;
        private List<String> referenceColumns = new ArrayList<>();
        
        public String toSqlDefinition() {
            return String.format("FOREIGN KEY (%s) REFERENCES %s(%s)",
                    String.join(", ", columns),
                    referenceTable,
                    String.join(", ", referenceColumns));
        }
    }
    
    public String generateCreateTableSql() {
        StringBuilder sql = new StringBuilder();
        sql.append("CREATE TABLE IF NOT EXISTS ").append(tableName).append(" (\n");
        
        // 添加列定义
        List<String> columnDefs = new ArrayList<>();
        for (ColumnDefinition column : columns) {
            columnDefs.add("  " + column.toSqlDefinition());
        }
        
        // 添加主键定义
        if (!primaryKeys.isEmpty()) {
            columnDefs.add("  PRIMARY KEY (" + String.join(", ", primaryKeys) + ")");
        }
        
        // 添加外键定义
        for (ForeignKeyDefinition fk : foreignKeys) {
            columnDefs.add("  " + fk.toSqlDefinition());
        }
        
        sql.append(String.join(",\n", columnDefs));
        sql.append("\n)");
        
        return sql.toString();
    }
    
    public String generateInsertSql(List<Map<String, Object>> records) {
        if (records == null || records.isEmpty()) {
            return "";
        }
        
        StringBuilder sql = new StringBuilder();
        sql.append("INSERT INTO ").append(tableName).append(" (");
        
        // 获取第一条记录的列名
        Map<String, Object> firstRecord = records.get(0);
        List<String> columnNames = new ArrayList<>(firstRecord.keySet());
        sql.append(String.join(", ", columnNames));
        
        sql.append(") VALUES ");
        
        // 添加所有记录的值
        List<String> valuesList = new ArrayList<>();
        for (Map<String, Object> record : records) {
            List<String> values = new ArrayList<>();
            for (String column : columnNames) {
                Object value = record.get(column);
                if (value == null) {
                    values.add("NULL");
                } else if (value instanceof String) {
                    values.add("'" + ((String) value).replace("'", "''") + "'");
                } else if (value instanceof java.util.Date) {
                    values.add("'" + new java.sql.Timestamp(((java.util.Date) value).getTime()) + "'");
                } else {
                    values.add(value.toString());
                }
            }
            valuesList.add("(" + String.join(", ", values) + ")");
        }
        
        sql.append(String.join(",\n", valuesList));
        
        return sql.toString();
    }
} 