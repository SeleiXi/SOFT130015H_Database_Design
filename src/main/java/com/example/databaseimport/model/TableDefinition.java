package com.example.databaseimport.model;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

public class TableDefinition {
    private String tableName;
    private List<ColumnDefinition> columns = new ArrayList<>();
    private List<String> primaryKeys = new ArrayList<>();
    private List<ForeignKeyDefinition> foreignKeys = new ArrayList<>();
    
    public TableDefinition() {
    }
    
    public TableDefinition(String tableName, List<ColumnDefinition> columns, List<String> primaryKeys, List<ForeignKeyDefinition> foreignKeys) {
        this.tableName = tableName;
        this.columns = columns;
        this.primaryKeys = primaryKeys;
        this.foreignKeys = foreignKeys;
    }
    
    // Getters and Setters
    public String getTableName() {
        return tableName;
    }
    
    public void setTableName(String tableName) {
        this.tableName = tableName;
    }
    
    public List<ColumnDefinition> getColumns() {
        return columns;
    }
    
    public void setColumns(List<ColumnDefinition> columns) {
        this.columns = columns;
    }
    
    public List<String> getPrimaryKeys() {
        return primaryKeys;
    }
    
    public void setPrimaryKeys(List<String> primaryKeys) {
        this.primaryKeys = primaryKeys;
    }
    
    public List<ForeignKeyDefinition> getForeignKeys() {
        return foreignKeys;
    }
    
    public void setForeignKeys(List<ForeignKeyDefinition> foreignKeys) {
        this.foreignKeys = foreignKeys;
    }
    
    // Builder replacement
    public static TableDefinitionBuilder builder() {
        return new TableDefinitionBuilder();
    }
    
    public static class TableDefinitionBuilder {
        private String tableName;
        private List<ColumnDefinition> columns = new ArrayList<>();
        private List<String> primaryKeys = new ArrayList<>();
        private List<ForeignKeyDefinition> foreignKeys = new ArrayList<>();
        
        public TableDefinitionBuilder tableName(String tableName) {
            this.tableName = tableName;
            return this;
        }
        
        public TableDefinitionBuilder columns(List<ColumnDefinition> columns) {
            this.columns = columns;
            return this;
        }
        
        public TableDefinitionBuilder primaryKeys(List<String> primaryKeys) {
            this.primaryKeys = primaryKeys;
            return this;
        }
        
        public TableDefinitionBuilder foreignKeys(List<ForeignKeyDefinition> foreignKeys) {
            this.foreignKeys = foreignKeys;
            return this;
        }
        
        public TableDefinition build() {
            return new TableDefinition(tableName, columns, primaryKeys, foreignKeys);
        }
    }
    
    public static class ColumnDefinition {
        private String name;
        private String type;
        private boolean nullable;
        private String defaultValue;
        private int position;
        
        public ColumnDefinition() {
        }
        
        public ColumnDefinition(String name, String type, boolean nullable, String defaultValue, int position) {
            this.name = name;
            this.type = type;
            this.nullable = nullable;
            this.defaultValue = defaultValue;
            this.position = position;
        }
        
        // Getters and Setters
        public String getName() {
            return name;
        }
        
        public void setName(String name) {
            this.name = name;
        }
        
        public String getType() {
            return type;
        }
        
        public void setType(String type) {
            this.type = type;
        }
        
        public boolean isNullable() {
            return nullable;
        }
        
        public void setNullable(boolean nullable) {
            this.nullable = nullable;
        }
        
        public String getDefaultValue() {
            return defaultValue;
        }
        
        public void setDefaultValue(String defaultValue) {
            this.defaultValue = defaultValue;
        }
        
        public int getPosition() {
            return position;
        }
        
        public void setPosition(int position) {
            this.position = position;
        }
        
        // Builder replacement
        public static ColumnDefinitionBuilder builder() {
            return new ColumnDefinitionBuilder();
        }
        
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
        
        // equals and hashCode
        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null || getClass() != o.getClass()) return false;
            ColumnDefinition that = (ColumnDefinition) o;
            return nullable == that.nullable &&
                    position == that.position &&
                    Objects.equals(name, that.name) &&
                    Objects.equals(type, that.type) &&
                    Objects.equals(defaultValue, that.defaultValue);
        }
        
        @Override
        public int hashCode() {
            return Objects.hash(name, type, nullable, defaultValue, position);
        }
        
        // toString
        @Override
        public String toString() {
            return "ColumnDefinition{" +
                    "name='" + name + '\'' +
                    ", type='" + type + '\'' +
                    ", nullable=" + nullable +
                    ", defaultValue='" + defaultValue + '\'' +
                    ", position=" + position +
                    '}';
        }
        
        public static class ColumnDefinitionBuilder {
            private String name;
            private String type;
            private boolean nullable;
            private String defaultValue;
            private int position;
            
            public ColumnDefinitionBuilder name(String name) {
                this.name = name;
                return this;
            }
            
            public ColumnDefinitionBuilder type(String type) {
                this.type = type;
                return this;
            }
            
            public ColumnDefinitionBuilder nullable(boolean nullable) {
                this.nullable = nullable;
                return this;
            }
            
            public ColumnDefinitionBuilder defaultValue(String defaultValue) {
                this.defaultValue = defaultValue;
                return this;
            }
            
            public ColumnDefinitionBuilder position(int position) {
                this.position = position;
                return this;
            }
            
            public ColumnDefinition build() {
                return new ColumnDefinition(name, type, nullable, defaultValue, position);
            }
        }
    }
    
    public static class ForeignKeyDefinition {
        private List<String> columns = new ArrayList<>();
        private String referenceTable;
        private List<String> referenceColumns = new ArrayList<>();
        
        public ForeignKeyDefinition() {
        }
        
        public ForeignKeyDefinition(List<String> columns, String referenceTable, List<String> referenceColumns) {
            this.columns = columns;
            this.referenceTable = referenceTable;
            this.referenceColumns = referenceColumns;
        }
        
        // Getters and Setters
        public List<String> getColumns() {
            return columns;
        }
        
        public void setColumns(List<String> columns) {
            this.columns = columns;
        }
        
        public String getReferenceTable() {
            return referenceTable;
        }
        
        public void setReferenceTable(String referenceTable) {
            this.referenceTable = referenceTable;
        }
        
        public List<String> getReferenceColumns() {
            return referenceColumns;
        }
        
        public void setReferenceColumns(List<String> referenceColumns) {
            this.referenceColumns = referenceColumns;
        }
        
        // Builder replacement
        public static ForeignKeyDefinitionBuilder builder() {
            return new ForeignKeyDefinitionBuilder();
        }
        
        public String toSqlDefinition() {
            return String.format("FOREIGN KEY (%s) REFERENCES %s(%s)",
                    String.join(", ", columns),
                    referenceTable,
                    String.join(", ", referenceColumns));
        }
        
        // equals and hashCode
        @Override
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null || getClass() != o.getClass()) return false;
            ForeignKeyDefinition that = (ForeignKeyDefinition) o;
            return Objects.equals(columns, that.columns) &&
                    Objects.equals(referenceTable, that.referenceTable) &&
                    Objects.equals(referenceColumns, that.referenceColumns);
        }
        
        @Override
        public int hashCode() {
            return Objects.hash(columns, referenceTable, referenceColumns);
        }
        
        // toString
        @Override
        public String toString() {
            return "ForeignKeyDefinition{" +
                    "columns=" + columns +
                    ", referenceTable='" + referenceTable + '\'' +
                    ", referenceColumns=" + referenceColumns +
                    '}';
        }
        
        public static class ForeignKeyDefinitionBuilder {
            private List<String> columns = new ArrayList<>();
            private String referenceTable;
            private List<String> referenceColumns = new ArrayList<>();
            
            public ForeignKeyDefinitionBuilder columns(List<String> columns) {
                this.columns = columns;
                return this;
            }
            
            public ForeignKeyDefinitionBuilder referenceTable(String referenceTable) {
                this.referenceTable = referenceTable;
                return this;
            }
            
            public ForeignKeyDefinitionBuilder referenceColumns(List<String> referenceColumns) {
                this.referenceColumns = referenceColumns;
                return this;
            }
            
            public ForeignKeyDefinition build() {
                return new ForeignKeyDefinition(columns, referenceTable, referenceColumns);
            }
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
    
    // equals and hashCode
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        TableDefinition that = (TableDefinition) o;
        return Objects.equals(tableName, that.tableName) &&
                Objects.equals(columns, that.columns) &&
                Objects.equals(primaryKeys, that.primaryKeys) &&
                Objects.equals(foreignKeys, that.foreignKeys);
    }
    
    @Override
    public int hashCode() {
        return Objects.hash(tableName, columns, primaryKeys, foreignKeys);
    }
    
    @Override
    public String toString() {
        return "TableDefinition{" +
                "tableName='" + tableName + '\'' +
                ", columns=" + columns +
                ", primaryKeys=" + primaryKeys +
                ", foreignKeys=" + foreignKeys +
                '}';
    }
} 