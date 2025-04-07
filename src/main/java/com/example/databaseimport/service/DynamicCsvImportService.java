package com.example.databaseimport.service;

import com.example.databaseimport.model.TableDefinition;
import com.opencsv.CSVReader;
import com.opencsv.CSVReaderBuilder;
import com.opencsv.exceptions.CsvValidationException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.FileReader;
import java.io.IOException;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.*;

@Service
public class DynamicCsvImportService {

    private static final Logger log = LoggerFactory.getLogger(DynamicCsvImportService.class);
    private final JdbcTemplate jdbcTemplate;
    private static final int BATCH_SIZE = 1000;
    private static final SimpleDateFormat DATE_FORMAT = new SimpleDateFormat("yyyy-MM-dd HH:mm");

    public DynamicCsvImportService(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    /**
     * 从CSV文件导入数据到数据库表
     *
     * @param csvFilePath CSV文件路径
     * @param tableDefinition 表定义
     * @param hasHeader CSV是否包含表头
     * @param columnMappings 列映射（CSV列位置 -> 表列名）
     * @param dataConverters 数据转换器（表列名 -> 转换函数）
     */
    @Transactional
    public void importCsvToTable(
            String csvFilePath,
            TableDefinition tableDefinition,
            boolean hasHeader,
            Map<Integer, String> columnMappings,
            Map<String, ColumnConverter> dataConverters) {
        
        try {
            // 创建表
            String createTableSql = tableDefinition.generateCreateTableSql();
            log.info("创建表SQL: {}", createTableSql);
            jdbcTemplate.execute(createTableSql);
            log.info("表[{}]创建成功", tableDefinition.getTableName());
            
            // 导入数据
            List<Map<String, Object>> records = readRecordsFromCsv(
                    csvFilePath, hasHeader, columnMappings, dataConverters);
            
            if (records.isEmpty()) {
                log.warn("没有从CSV读取到有效数据");
                return;
            }
            
            // 分批插入数据
            for (int i = 0; i < records.size(); i += BATCH_SIZE) {
                int end = Math.min(i + BATCH_SIZE, records.size());
                List<Map<String, Object>> batch = records.subList(i, end);
                
                String insertSql = tableDefinition.generateInsertSql(batch);
                log.debug("执行插入SQL: {}", insertSql);
                
                try {
                    jdbcTemplate.update(insertSql);
                    log.info("成功插入批次数据: {} 到 {}", i, end - 1);
                } catch (Exception e) {
                    log.error("批量插入数据失败: {}", e.getMessage());
                    
                    // 单条尝试插入
                    for (Map<String, Object> record : batch) {
                        try {
                            String singleInsertSql = tableDefinition.generateInsertSql(Collections.singletonList(record));
                            jdbcTemplate.update(singleInsertSql);
                        } catch (Exception ex) {
                            log.error("单条数据插入失败: {}", record, ex);
                        }
                    }
                }
            }
            
            // 验证导入结果
            int count = jdbcTemplate.queryForObject(
                    "SELECT COUNT(*) FROM " + tableDefinition.getTableName(), Integer.class);
            log.info("表[{}]数据导入完成，共导入 {} 条记录", tableDefinition.getTableName(), count);
            
        } catch (Exception e) {
            log.error("导入数据到表[{}]失败", tableDefinition.getTableName(), e);
            throw new RuntimeException("导入数据失败", e);
        }
    }
    
    /**
     * 从CSV文件读取记录
     */
    private List<Map<String, Object>> readRecordsFromCsv(
            String csvFilePath,
            boolean hasHeader,
            Map<Integer, String> columnMappings,
            Map<String, ColumnConverter> dataConverters) throws IOException, CsvValidationException {
        
        List<Map<String, Object>> records = new ArrayList<>();
        
        try (CSVReader reader = new CSVReaderBuilder(new FileReader(csvFilePath))
                .withSkipLines(hasHeader ? 1 : 0)
                .build()) {
            
            String[] line;
            while ((line = reader.readNext()) != null) {
                if (line.length == 0) {
                    continue;
                }
                
                Map<String, Object> record = new HashMap<>();
                
                for (Map.Entry<Integer, String> mapping : columnMappings.entrySet()) {
                    int columnIndex = mapping.getKey();
                    String columnName = mapping.getValue();
                    
                    if (columnIndex >= line.length) {
                        log.warn("CSV行数据列数不足，跳过列映射: {} -> {}", columnIndex, columnName);
                        continue;
                    }
                    
                    String rawValue = line[columnIndex].trim();
                    
                    // 应用数据转换器
                    ColumnConverter converter = dataConverters.get(columnName);
                    if (converter != null) {
                        try {
                            Object convertedValue = converter.convert(rawValue);
                            record.put(columnName, convertedValue);
                        } catch (Exception e) {
                            log.error("转换列[{}]的值[{}]失败: {}", columnName, rawValue, e.getMessage());
                            record.put(columnName, null);
                        }
                    } else {
                        record.put(columnName, rawValue);
                    }
                }
                
                if (!record.isEmpty()) {
                    records.add(record);
                }
            }
        }
        
        return records;
    }
    
    /**
     * 获取日期转换器
     */
    public static ColumnConverter getDateConverter() {
        return value -> {
            if (value == null || value.isEmpty()) {
                return null;
            }
            return DATE_FORMAT.parse(value);
        };
    }
    
    /**
     * 获取整数转换器
     */
    public static ColumnConverter getIntConverter() {
        return value -> {
            if (value == null || value.isEmpty()) {
                return null;
            }
            return Integer.parseInt(value);
        };
    }
    
    /**
     * 获取字符串转换器(去除引号)
     */
    public static ColumnConverter getStringConverter() {
        return value -> {
            if (value == null) {
                return null;
            }
            return value.replace("\"", "").trim();
        };
    }
    
    /**
     * 列数据转换器接口
     */
    @FunctionalInterface
    public interface ColumnConverter {
        Object convert(String value) throws ParseException;
    }
} 